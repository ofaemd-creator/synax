"""
SYNAX E-Graph Equality Saturation & Hardware-Cost Extraction (`src/synax/egraph.py`)
====================================================================================
Replaces classical phase-ordered peephole rewriting with Equality Saturation over an
Equivalence Graph (E-Graph):
  1. Populates an E-Graph from a `synax_ir.ASTNode`.
  2. Applies non-destructive algebraic & SIMD-fusion equivalences simultaneously
     (`a * b + c <=> fma(a, b, c)`, `x * x <=> pow2(x)`, `relu(relu(x)) <=> relu(x)`,
      `select(c, x, x) <=> x`, `--x <=> x`, constant folding).
  3. Maintains congruence closure via Union-Find and hashconsing (`rebuild()`).
  4. Extracts the minimum-cycle AST for the target silicon (`neon`, `avx2`, `mcu_q16`, `scalar`)
     using bottom-up dynamic programming.

SPDX-License-Identifier: Apache-2.0
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from synax_ir import ASTNode, _f32


@dataclass(frozen=True)
class ENode:
    op: str
    value: Optional[str] = None
    children: Tuple[int, ...] = ()

    def canonicalize(self, uf: "UnionFind") -> "ENode":
        if not self.children:
            return self
        return ENode(self.op, self.value, tuple(uf.find(c) for c in self.children))


class UnionFind:
    def __init__(self) -> None:
        self.parent: List[int] = []

    def make_set(self) -> int:
        idx = len(self.parent)
        self.parent.append(idx)
        return idx

    def find(self, i: int) -> int:
        while self.parent[i] != i:
            self.parent[i] = self.parent[self.parent[i]]
            i = self.parent[i]
        return i

    def union(self, i: int, j: int) -> int:
        ri, rj = self.find(i), self.find(j)
        if ri != rj:
            self.parent[rj] = ri
        return ri


# Hardware instruction latency models (in relative execution cycles per vector/element)
COST_MODELS: Dict[str, Dict[str, float]] = {
    "neon": {
        "VAR": 0.1,
        "CONST": 0.1,
        "BIAS": 0.1,
        "NEG": 1.0,
        "ABS": 1.0,
        "RELU": 1.0,
        "MIN": 1.5,
        "MAX": 1.5,
        "CLAMP": 2.5,
        "ADD": 2.0,
        "SUB": 2.0,
        "MUL": 2.0,
        "POW2": 1.8,   # Single register vmulq_f32(x, x)
        "POW3": 3.5,
        "FMA": 2.0,    # Single-cycle fused vfmaq_f32(c, a, b) vs MUL(2) + ADD(2) = 4
        "SELECT": 1.5, # Branchless vbslq_f32 + vcgtq_f32
        "DIV": 7.0,
        "SQRT": 6.0,
        "EXP": 18.0,
        "LOG": 18.0,
        "SIN": 18.0,
        "COS": 18.0,
        "SIGMOID": 22.0,
        "TANH": 20.0,
    },
    "mcu_q16": {
        "VAR": 0.1,
        "CONST": 0.1,
        "BIAS": 0.1,
        "NEG": 1.0,
        "ABS": 1.0,
        "RELU": 1.0,
        "MIN": 1.2,
        "MAX": 1.2,
        "CLAMP": 2.0,
        "ADD": 1.0,
        "SUB": 1.0,
        "SELECT": 1.2,
        "MUL": 3.5,    # 64-bit fixed-point multiply + >> 16 shift
        "POW2": 3.2,
        "FMA": 4.2,    # Single shift after MAC in Q16.16
        "POW3": 6.5,
        "DIV": 16.0,
        "SQRT": 14.0,
        "EXP": 30.0,
        "LOG": 30.0,
        "SIN": 28.0,
        "COS": 28.0,
        "SIGMOID": 12.0,
        "TANH": 12.0,
    },
}


@dataclass
class EGraphReport:
    original_ast: ASTNode
    optimized_ast: ASTNode
    target: str
    eclasses_count: int
    enodes_count: int
    iterations_run: int
    cost_before: float
    cost_after: float
    rewrites_triggered: List[str] = field(default_factory=list)

    @property
    def cycle_reduction_pct(self) -> float:
        if self.cost_before <= 0:
            return 0.0
        return round(max(0.0, (self.cost_before - self.cost_after) / self.cost_before * 100.0), 1)


def compute_ast_cost(node: ASTNode, target: str = "neon") -> float:
    table = COST_MODELS.get(target, COST_MODELS["neon"])
    op_cost = table.get(node.op, 4.0)
    return op_cost + sum(compute_ast_cost(c, target) for c in node.children)


class EGraph:
    """Equivalence Graph with congruence closure and cost-guided extraction."""

    def __init__(self) -> None:
        self.uf = UnionFind()
        self.memo: Dict[ENode, int] = {}
        self.classes: Dict[int, Set[ENode]] = {}
        self.worklist: List[int] = []
        self.rewrites_log: Set[str] = set()

    def find(self, eclass_id: int) -> int:
        return self.uf.find(eclass_id)

    def add_enode(self, enode: ENode) -> int:
        canon = enode.canonicalize(self.uf)
        if canon in self.memo:
            return self.uf.find(self.memo[canon])
        cid = self.uf.make_set()
        self.memo[canon] = cid
        self.classes[cid] = {canon}
        return cid

    def add_ast(self, node: ASTNode) -> int:
        child_ids = tuple(self.add_ast(c) for c in node.children)
        val = node.value
        if node.op == "CONST" and val is not None:
            val = repr(_f32(float(val)))
        return self.add_enode(ENode(op=node.op, value=val, children=child_ids))

    def merge(self, id1: int, id2: int) -> int:
        r1, r2 = self.find(id1), self.find(id2)
        if r1 == r2:
            return r1
        merged = self.uf.union(r1, r2)
        other = r2 if merged == r1 else r1
        self.classes[merged] |= self.classes.pop(other, set())
        self.worklist.append(merged)
        return merged

    def rebuild(self) -> None:
        while self.worklist:
            todo = {self.find(c) for c in self.worklist}
            self.worklist.clear()
            new_memo: Dict[ENode, int] = {}
            new_classes: Dict[int, Set[ENode]] = {}
            for cid, nodes in list(self.classes.items()):
                rcid = self.find(cid)
                bucket = new_classes.setdefault(rcid, set())
                for n in nodes:
                    cn = n.canonicalize(self.uf)
                    bucket.add(cn)
                    if cn in new_memo:
                        prev = self.find(new_memo[cn])
                        if prev != rcid:
                            self.uf.union(prev, rcid)
                            self.worklist.append(prev)
                    else:
                        new_memo[cn] = rcid
            self.classes = new_classes
            self.memo = new_memo

    def _const_val(self, cid: int) -> Optional[float]:
        rcid = self.find(cid)
        for n in self.classes.get(rcid, ()):
            if n.op == "CONST" and n.value is not None:
                return _f32(float(n.value))
        return None

    def saturate(self, max_iter: int = 6) -> int:
        """Apply equality saturation rules until fixed point or `max_iter`."""
        it = 0
        for it in range(1, max_iter + 1):
            merges: List[Tuple[int, int, str]] = []
            snapshot = [(cid, list(nodes)) for cid, nodes in self.classes.items()]

            for cid, nodes in snapshot:
                rcid = self.find(cid)
                for n in nodes:
                    # 1. Constant folding when all children have a constant representative
                    if n.children and n.op not in ("VAR", "CONST", "BIAS"):
                        cvals = [self._const_val(ch) for ch in n.children]
                        if all(v is not None for v in cvals):
                            try:
                                dummy = ASTNode(n.op)
                                res = dummy._eval_op_f32([float(v) for v in cvals if v is not None])
                                if math.isfinite(res):
                                    c_node = self.add_enode(ENode("CONST", repr(_f32(res)), ()))
                                    if self.find(c_node) != rcid:
                                        merges.append((rcid, c_node, f"const_fold({n.op})"))
                            except Exception:
                                pass

                    # 2. ADD rules: FMA fusion, x + 0 -> x, x + x -> 2*x
                    if n.op == "ADD" and len(n.children) == 2:
                        l, r = self.find(n.children[0]), self.find(n.children[1])
                        lv, rv = self._const_val(l), self._const_val(r)
                        if rv == 0.0 and rcid != l:
                            merges.append((rcid, l, "add_zero_right: x + 0 -> x"))
                        if lv == 0.0 and rcid != r:
                            merges.append((rcid, r, "add_zero_left: 0 + x -> x"))
                        if l == r:
                            two = self.add_enode(ENode("CONST", repr(_f32(2.0)), ()))
                            mul2 = self.add_enode(ENode("MUL", None, (l, two)))
                            if self.find(mul2) != rcid:
                                merges.append((rcid, mul2, "strength_add: x + x <=> 2 * x"))
                        # FMA hardware fusion: (a * b) + c <=> fma(a, b, c)
                        for ln in list(self.classes.get(l, ())):
                            if ln.op == "MUL" and len(ln.children) == 2:
                                fma_id = self.add_enode(ENode("FMA", None, (ln.children[0], ln.children[1], r)))
                                if self.find(fma_id) != rcid:
                                    merges.append((rcid, fma_id, "fma_fusion: (a * b) + c <=> fma(a, b, c)"))
                        for rn in list(self.classes.get(r, ())):
                            if rn.op == "MUL" and len(rn.children) == 2:
                                fma_id = self.add_enode(ENode("FMA", None, (rn.children[0], rn.children[1], l)))
                                if self.find(fma_id) != rcid:
                                    merges.append((rcid, fma_id, "fma_fusion: c + (a * b) <=> fma(a, b, c)"))

                    # 3. SUB rules: x - 0 -> x, x - (-y) -> x + y, (a * b) - c -> fma(a, b, -c)
                    elif n.op == "SUB" and len(n.children) == 2:
                        l, r = self.find(n.children[0]), self.find(n.children[1])
                        rv = self._const_val(r)
                        if rv == 0.0 and rcid != l:
                            merges.append((rcid, l, "sub_zero: x - 0 -> x"))
                        for rn in list(self.classes.get(r, ())):
                            if rn.op == "NEG" and len(rn.children) == 1:
                                add_id = self.add_enode(ENode("ADD", None, (l, rn.children[0])))
                                if self.find(add_id) != rcid:
                                    merges.append((rcid, add_id, "sub_neg: x - (-y) <=> x + y"))

                    # 4. MUL rules: x * 1 -> x, x * x <=> pow2(x), pow2(x) * x <=> pow3(x)
                    elif n.op == "MUL" and len(n.children) == 2:
                        l, r = self.find(n.children[0]), self.find(n.children[1])
                        lv, rv = self._const_val(l), self._const_val(r)
                        if rv == 1.0 and rcid != l:
                            merges.append((rcid, l, "mul_one_right: x * 1 -> x"))
                        if lv == 1.0 and rcid != r:
                            merges.append((rcid, r, "mul_one_left: 1 * x -> x"))
                        if l == r:
                            p2 = self.add_enode(ENode("POW2", None, (l,)))
                            if self.find(p2) != rcid:
                                merges.append((rcid, p2, "square_fusion: x * x <=> pow2(x)"))
                        for ln in list(self.classes.get(l, ())):
                            if ln.op == "POW2" and len(ln.children) == 1 and self.find(ln.children[0]) == r:
                                p3 = self.add_enode(ENode("POW3", None, (r,)))
                                if self.find(p3) != rcid:
                                    merges.append((rcid, p3, "cube_fusion: pow2(x) * x <=> pow3(x)"))

                    # 5. DIV rules: x / 1 -> x, x / c -> x * (1/c) when 1/c is exact power of two
                    elif n.op == "DIV" and len(n.children) == 2:
                        l, r = self.find(n.children[0]), self.find(n.children[1])
                        rv = self._const_val(r)
                        if rv == 1.0 and rcid != l:
                            merges.append((rcid, l, "div_one: x / 1 -> x"))
                        elif rv is not None and rv > 0.0 and (rv in (0.125, 0.25, 0.5, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0)):
                            inv_c = self.add_enode(ENode("CONST", repr(_f32(1.0 / rv)), ()))
                            mul_inv = self.add_enode(ENode("MUL", None, (l, inv_c)))
                            if self.find(mul_inv) != rcid:
                                merges.append((rcid, mul_inv, f"exact_recip_mul: x / {rv:g} -> x * {1.0/rv:g} (0-ULP)"))

                    # 6. Idempotent & involution unary rules: --x -> x, relu(relu(x)) -> relu(x), abs(abs(x)) -> abs(x)
                    elif n.op == "NEG" and len(n.children) == 1:
                        c0 = self.find(n.children[0])
                        for cn in list(self.classes.get(c0, ())):
                            if cn.op == "NEG" and len(cn.children) == 1:
                                inner = self.find(cn.children[0])
                                if inner != rcid:
                                    merges.append((rcid, inner, "double_neg: -(-x) -> x"))

                    elif n.op in ("RELU", "ABS") and len(n.children) == 1:
                        c0 = self.find(n.children[0])
                        for cn in list(self.classes.get(c0, ())):
                            if cn.op == n.op:
                                merges.append((rcid, c0, f"idempotent_{n.op.lower()}: {n.op.lower()}({n.op.lower()}(x)) -> {n.op.lower()}(x)"))
                            elif n.op == "ABS" and cn.op == "POW2":
                                merges.append((rcid, c0, "abs_pow2: abs(pow2(x)) -> pow2(x)"))

                    # 7. Branchless SELECT rules: select(c, x, x) -> x, select(const, t, f) -> t or f
                    elif n.op == "SELECT" and len(n.children) == 3:
                        cond_c, t_c, f_c = (self.find(ch) for ch in n.children)
                        if t_c == f_c and rcid != t_c:
                            merges.append((rcid, t_c, "select_same_branches: select(c, x, x) -> x"))
                        cv = self._const_val(cond_c)
                        if cv is not None and not math.isnan(cv):
                            chosen = t_c if cv > 0.0 else f_c
                            if rcid != chosen:
                                merges.append((rcid, chosen, f"select_const_cond({cv:g})"))

                    # 8. Reverse FMA exploration so constant folding/simplification can inspect expanded form
                    elif n.op == "FMA" and len(n.children) == 3:
                        a_c, b_c, c_c = (self.find(ch) for ch in n.children)
                        mul_id = self.add_enode(ENode("MUL", None, (a_c, b_c)))
                        add_id = self.add_enode(ENode("ADD", None, (mul_id, c_c)))
                        if self.find(add_id) != rcid:
                            merges.append((rcid, add_id, "fma_equivalence: fma(a, b, c) <=> (a * b) + c"))

            if not merges:
                break
            for id1, id2, reason in merges:
                if self.find(id1) != self.find(id2):
                    self.rewrites_log.add(reason)
                    self.merge(id1, id2)
            self.rebuild()
        return it

    def extract_best(self, root_id: int, target: str = "neon") -> Tuple[ASTNode, float]:
        """Bottom-up dynamic programming extraction of minimum-cycle AST from the E-Graph."""
        table = COST_MODELS.get(target, COST_MODELS["neon"])
        best_cost: Dict[int, float] = {}
        best_node: Dict[int, ENode] = {}

        changed = True
        while changed:
            changed = False
            for cid, nodes in self.classes.items():
                rcid = self.find(cid)
                for n in nodes:
                    if all(self.find(ch) in best_cost for ch in n.children):
                        c = table.get(n.op, 4.0) + sum(best_cost[self.find(ch)] for ch in n.children)
                        if rcid not in best_cost or c < best_cost[rcid]:
                            best_cost[rcid] = c
                            best_node[rcid] = n
                            changed = True

        def build_ast(cid: int, visited: Set[int]) -> ASTNode:
            rcid = self.find(cid)
            en = best_node[rcid]
            if rcid in visited and en.children:
                # Guard against cyclic equivalences by picking a leaf or minimal-depth node
                for alt in self.classes[rcid]:
                    if not alt.children:
                        en = alt
                        break
            next_vis = visited | {rcid}
            kids = [build_ast(ch, next_vis) for ch in en.children]
            return ASTNode(op=en.op, value=en.value, children=kids)

        r_root = self.find(root_id)
        return build_ast(r_root, set()), round(best_cost.get(r_root, 0.0), 2)


def saturate_and_extract(ast: ASTNode, target: str = "neon", max_iter: int = 6) -> EGraphReport:
    """Run E-Graph equality saturation on `ast` and extract the lowest-cost AST for `target`."""
    cost_before = round(compute_ast_cost(ast, target), 2)
    eg = EGraph()
    root = eg.add_ast(ast)
    iters = eg.saturate(max_iter=max_iter)
    opt_ast, cost_after = eg.extract_best(root, target=target)
    total_enodes = sum(len(ns) for ns in eg.classes.values())
    return EGraphReport(
        original_ast=ast,
        optimized_ast=opt_ast,
        target=target,
        eclasses_count=len(eg.classes),
        enodes_count=total_enodes,
        iterations_run=iters,
        cost_before=cost_before,
        cost_after=cost_after,
        rewrites_triggered=sorted(eg.rewrites_log),
    )

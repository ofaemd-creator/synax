"""SynaxLLM training, local inference and owned-model API commands."""

from __future__ import annotations
import argparse
import json
from pathlib import Path


def main() -> None:
    """Run offline model tools; never download a pretrained model."""
    parser = argparse.ArgumentParser(prog="synax-llm")
    sub = parser.add_subparsers(dest="command", required=True)
    training = sub.add_parser("train")
    training.add_argument("--data", type=Path, required=True)
    training.add_argument("--validation", type=Path, required=True)
    training.add_argument("--output", type=Path, required=True)
    training.add_argument("--steps", type=int, default=200)
    training.add_argument("--seed", type=int, default=42)
    training.add_argument("--device", choices=["cpu", "mps", "cuda"], default="cpu")
    training.add_argument("--context", type=int, default=256)
    generation = sub.add_parser("generate")
    generation.add_argument("--model", type=Path, required=True)
    generation.add_argument("--prompt", required=True)
    generation.add_argument("--max-tokens", type=int, default=128)
    serving = sub.add_parser("serve")
    serving.add_argument("--model", type=Path, required=True)
    serving.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    match args.command:
        case "train":
            from .model import ModelSpec
            from .training import TrainingRun, train

            report = train(
                TrainingRun(
                    args.data,
                    args.validation,
                    args.output,
                    args.steps,
                    args.seed,
                    args.device,
                ),
                ModelSpec(context=args.context),
            )
            print(json.dumps(report, indent=2))
        case "generate":
            from .runtime import LocalModel

            model = LocalModel(args.model)
            print(
                model.generate(
                    [{"role": "user", "content": args.prompt}], args.max_tokens
                )
            )
        case "serve":
            from synax.assistant.server import serve

            serve(args.model, args.port)


if __name__ == "__main__":
    main()

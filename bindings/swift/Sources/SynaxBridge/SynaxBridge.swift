//
//  SynaxBridge.swift
//  SYNAX Native Swift Bridge for macOS & iOS (Xcode)
//
//  Provides asynchronous, actor-isolated communication with the SYNAX
//  Neuro-Symbolic compiler engine via JSON-RPC stdio.
//
//  Copyright © 2026 Dr. Ömer Faruk Aydın. All rights reserved.
//  SPDX-License-Identifier: Apache-2.0
//

import Foundation

// MARK: - Data Models

public struct SynaxChatResponse: Sendable {
    public let text: String
    public let code: String?
    public let language: String?
    public let action: String?
    public let rawMetadata: [String: Any]?

    public init(
        text: String,
        code: String? = nil,
        language: String? = nil,
        action: String? = nil,
        rawMetadata: [String: Any]? = nil
    ) {
        self.text = text
        self.code = code
        self.language = language
        self.action = action
        self.rawMetadata = rawMetadata
    }
}

public struct SynaxSkillResponse: Sendable {
    public let concept: String
    public let humanFormula: String
    public let generation: Int
    public let sha256: String
    public let cScalar: String?
    public let cNeon: String?
}

public enum SynaxBridgeError: LocalizedError {
    case processNotRunning
    case launchFailed(String)
    case invalidResponse(String)
    case requestTimeout
    case jsonEncodingError
    case serverError(String)

    public var errorDescription: String? {
        switch self {
        case .processNotRunning:
            return "SYNAX backend işlemi çalışmıyor."
        case .launchFailed(let msg):
            return "SYNAX başlatılamadı: \(msg)"
        case .invalidResponse(let msg):
            return "Geçersiz SYNAX yanıtı: \(msg)"
        case .requestTimeout:
            return "SYNAX sorgusu zaman aşımına uğradı."
        case .jsonEncodingError:
            return "JSON serileştirme hatası."
        case .serverError(let msg):
            return "SYNAX sunucu hatası: \(msg)"
        }
    }
}

// MARK: - SynaxBridge Actor

public actor SynaxBridge {
    private var process: Process?
    private var stdinPipe: Pipe?
    private var stdoutPipe: Pipe?
    private var nextRequestId: Int = 1
    private var pendingRequests: [Int: CheckedContinuation<[String: Any], Error>] = [:]
    private var isStarted = false

    public let synaxScriptPath: String
    public let pythonPath: String

    /// Initializer with custom script and python executable paths.
    public init(
        synaxScriptPath: String? = nil,
        pythonPath: String? = nil
    ) {
        // Otomatik yol tespiti:
        if let script = synaxScriptPath {
            self.synaxScriptPath = script
        } else {
            // Varsayılan çalışma alanı veya Desktop hub tespiti
            let defaultScratch = ("~/.gemini/antigravity/scratch/synax/synax_chat.py" as NSString).expandingTildeInPath
            let desktopHub = ("~/Desktop/AI modeller/SYNAX/proje/synax_chat.py" as NSString).expandingTildeInPath
            if FileManager.default.fileExists(atPath: defaultScratch) {
                self.synaxScriptPath = defaultScratch
            } else if FileManager.default.fileExists(atPath: desktopHub) {
                self.synaxScriptPath = desktopHub
            } else {
                self.synaxScriptPath = defaultScratch
            }
        }

        // Python yol tespiti
        if let py = pythonPath {
            self.pythonPath = py
        } else if FileManager.default.fileExists(atPath: "/opt/homebrew/bin/python3") {
            self.pythonPath = "/opt/homebrew/bin/python3"
        } else if FileManager.default.fileExists(atPath: "/usr/local/bin/python3") {
            self.pythonPath = "/usr/local/bin/python3"
        } else {
            self.pythonPath = "/usr/bin/python3"
        }
    }

    deinit {
        process?.terminate()
    }

    // MARK: - Process Lifecycle

    public func start() throws {
        guard !isStarted else { return }

        guard FileManager.default.fileExists(atPath: synaxScriptPath) else {
            throw SynaxBridgeError.launchFailed("synax_chat.py bulunamadı: \(synaxScriptPath)")
        }

        let proc = Process()
        proc.executableURL = URL(fileURLWithPath: pythonPath)
        proc.arguments = [synaxScriptPath, "--json-rpc"]

        let scriptDir = (synaxScriptPath as NSString).deletingLastPathComponent
        proc.currentDirectoryURL = URL(fileURLWithPath: scriptDir)

        // Environment variables
        var env = ProcessInfo.processInfo.environment
        env["PYTHONUNBUFFERED"] = "1"
        proc.environment = env

        let inPipe = Pipe()
        let outPipe = Pipe()
        let errPipe = Pipe()

        proc.standardInput = inPipe
        proc.standardOutput = outPipe
        proc.standardError = errPipe

        do {
            try proc.run()
        } catch {
            throw SynaxBridgeError.launchFailed(error.localizedDescription)
        }

        self.process = proc
        self.stdinPipe = inPipe
        self.stdoutPipe = outPipe
        self.isStarted = true

        // Arka planda gelen satırları dinleme
        Task.detached { [weak self] in
            await self?.listenToOutput(pipe: outPipe)
        }
    }

    public func stop() {
        process?.terminate()
        process = nil
        stdinPipe = nil
        stdoutPipe = nil
        isStarted = false

        for (_, cont) in pendingRequests {
            cont.resume(throwing: SynaxBridgeError.processNotRunning)
        }
        pendingRequests.removeAll()
    }

    // MARK: - High-Level API

    /// Send a natural language prompt or command to SYNAX.
    public func sendMessage(_ text: String, context: [String: Any]? = nil) async throws -> SynaxChatResponse {
        try startIfNeeded()

        let reqId = nextRequestId
        nextRequestId += 1

        var params: [String: Any] = ["text": text]
        if let context = context {
            params["context"] = context
        }

        let dict = try await sendRpc(id: reqId, method: "chat", params: params)
        let resText = dict["text"] as? String ?? ""
        let code = dict["code"] as? String
        let lang = dict["language"] as? String
        let action = dict["action"] as? String
        let meta = dict["metadata"] as? [String: Any]

        return SynaxChatResponse(
            text: resText,
            code: code,
            language: lang,
            action: action,
            rawMetadata: meta
        )
    }

    /// Teach SYNAX a new autopoietic skill: "kendine şu beceriyi edin: concept = formula".
    public func teachSkill(concept: String, formula: String) async throws -> SynaxSkillResponse {
        try startIfNeeded()

        let reqId = nextRequestId
        nextRequestId += 1

        let params: [String: Any] = ["concept": concept, "formula": formula]
        let dict = try await sendRpc(id: reqId, method: "teach", params: params)

        return SynaxSkillResponse(
            concept: dict["concept"] as? String ?? concept,
            humanFormula: dict["human_formula"] as? String ?? formula,
            generation: dict["generation"] as? Int ?? 1,
            sha256: dict["sha256"] as? String ?? "",
            cScalar: dict["c_scalar"] as? String,
            cNeon: dict["c_neon"] as? String
        )
    }

    /// Run the 4-variant TYCON Evolution Arena on a given kernel code string or file.
    public func evolveKernel(code: String) async throws -> String {
        try startIfNeeded()

        let reqId = nextRequestId
        nextRequestId += 1

        let params: [String: Any] = ["code": code]
        let dict = try await sendRpc(id: reqId, method: "evolve", params: params)
        return dict["markdown"] as? String ?? "Evrim tamamlandı."
    }

    /// Ping the backend to check readiness.
    public func ping() async throws -> Bool {
        try startIfNeeded()
        let reqId = nextRequestId
        nextRequestId += 1
        let dict = try await sendRpc(id: reqId, method: "ping", params: [:])
        return dict["status"] as? String == "ok"
    }

    // MARK: - Internal RPC Dispatch

    private func startIfNeeded() throws {
        if !isStarted || process?.isRunning != true {
            try start()
        }
    }

    private func sendRpc(id: Int, method: String, params: [String: Any]) async throws -> [String: Any] {
        guard let inPipe = stdinPipe, let proc = process, proc.isRunning else {
            throw SynaxBridgeError.processNotRunning
        }

        let payload: [String: Any] = [
            "jsonrpc": "2.0",
            "id": id,
            "method": method,
            "params": params
        ]

        let data = try JSONSerialization.data(withJSONObject: payload, options: [])
        guard var jsonString = String(data: data, encoding: .utf8) else {
            throw SynaxBridgeError.jsonEncodingError
        }
        jsonString.append("\n")

        guard let writeData = jsonString.data(using: .utf8) else {
            throw SynaxBridgeError.jsonEncodingError
        }

        return try await withCheckedThrowingContinuation { continuation in
            self.pendingRequests[id] = continuation
            inPipe.fileHandleForWriting.write(writeData)
        }
    }

    private func listenToOutput(pipe: Pipe) {
        let handle = pipe.fileHandleForReading
        var buffer = Data()

        while true {
            let chunk = handle.availableData
            if chunk.isEmpty {
                break
            }
            buffer.append(chunk)

            while let newlineIndex = buffer.firstIndex(of: UInt8(ascii: "\n")) {
                let lineData = buffer.subdata(in: 0..<newlineIndex)
                buffer.removeSubrange(0...newlineIndex)

                if let jsonString = String(data: lineData, encoding: .utf8)?.trimmingCharacters(in: .whitespacesAndNewlines),
                   !jsonString.isEmpty {
                    self.handleIncomingLine(jsonString)
                }
            }
        }
    }

    private func handleIncomingLine(_ line: String) {
        guard let data = line.data(using: .utf8) else { return }
        guard let obj = try? JSONSerialization.jsonObject(with: data, options: []) as? [String: Any] else {
            return
        }

        if let reqId = obj["id"] as? Int, let continuation = pendingRequests.removeValue(forKey: reqId) {
            if let errorObj = obj["error"] as? [String: Any], let msg = errorObj["message"] as? String {
                continuation.resume(throwing: SynaxBridgeError.serverError(msg))
            } else if let result = obj["result"] as? [String: Any] {
                continuation.resume(returning: result)
            } else {
                continuation.resume(returning: obj)
            }
        }
    }
}

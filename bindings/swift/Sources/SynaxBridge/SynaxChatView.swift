//
//  SynaxChatView.swift
//  SYNAX Native SwiftUI Pair-Programmer & LLM Chat Interface
//
//  Designed for Xcode 15/16, macOS 13+ and iOS 16+.
//  Directly communicates with the SYNAX Neuro-Symbolic compiler via SynaxBridge.
//
//  Copyright © 2026 Dr. Ömer Faruk Aydın. All rights reserved.
//  SPDX-License-Identifier: Apache-2.0
//

import SwiftUI

// MARK: - Message Model

public struct SynaxChatMessage: Identifiable, Equatable {
    public let id = UUID()
    public let isUser: Bool
    public let text: String
    public let code: String?
    public let language: String?
    public let action: String?
    public let date: Date = Date()
}

// MARK: - ViewModel

@MainActor
public class SynaxChatViewModel: ObservableObject {
    @Published public var messages: [SynaxChatMessage] = []
    @Published public var inputText: String = ""
    @Published public var isBusy: Bool = false
    @Published public var isConnected: Bool = false
    @Published public var errorMessage: String? = nil

    private let bridge: SynaxBridge

    public init(bridge: SynaxBridge = SynaxBridge()) {
        self.bridge = bridge

        // Karşılama mesajı
        messages.append(
            SynaxChatMessage(
                isUser: false,
                text: "👋 **SYNAX Code (v0.7.0)**'a hoş geldiniz Dr. Aydın!\n\n" +
                      "Klinik algoritmalarınızı sembolik formüllere dökebilir, donanım hızlandırmalı " +
                      "ARM64 NEON çekirdekleri üretebilir ve Xcode projelerinizle C-ABI üzerinden " +
                      "doğrudan entegre olabilirsiniz.",
                code: nil,
                language: nil,
                action: "welcome"
            )
        )

        Task {
            await checkConnection()
        }
    }

    public func checkConnection() async {
        do {
            let ok = try await bridge.ping()
            self.isConnected = ok
        } catch {
            self.isConnected = false
        }
    }

    public func sendMessage(_ prompt: String? = nil) {
        let textToSend = (prompt ?? inputText).trimmingCharacters(in: .whitespacesAndNewlines)
        guard !textToSend.isEmpty, !isBusy else { return }

        if prompt == nil {
            inputText = ""
        }

        // Kullanıcı mesajını ekle
        messages.append(SynaxChatMessage(isUser: true, text: textToSend, code: nil, language: nil, action: nil))
        isBusy = true
        errorMessage = nil

        Task {
            do {
                let response = try await bridge.sendMessage(textToSend)
                messages.append(
                    SynaxChatMessage(
                        isUser: false,
                        text: response.text,
                        code: response.code,
                        language: response.language,
                        action: response.action
                    )
                )
                isConnected = true
            } catch {
                errorMessage = error.localizedDescription
                messages.append(
                    SynaxChatMessage(
                        isUser: false,
                        text: "⚠️ **Hata Oluştu:** \(error.localizedDescription)\n\n" +
                              "Lütfen SYNAX Python çalışma zamanının kurulu olduğundan emin olun.",
                        code: nil,
                        language: nil,
                        action: "error"
                    )
                )
                isConnected = false
            }
            isBusy = false
        }
    }

    public func evolveKernel(_ code: String) {
        guard !isBusy else { return }
        isBusy = true
        Task {
            do {
                let markdown = try await bridge.evolveKernel(code: code)
                messages.append(
                    SynaxChatMessage(
                        isUser: false,
                        text: markdown,
                        code: nil,
                        language: "markdown",
                        action: "evolved"
                    )
                )
            } catch {
                errorMessage = error.localizedDescription
            }
            isBusy = false
        }
    }
}

// MARK: - Main SwiftUI View

public struct SynaxChatView: View {
    @StateObject private var viewModel: SynaxChatViewModel
    @FocusState private var isInputFocused: Bool

    public init(viewModel: SynaxChatViewModel = SynaxChatViewModel()) {
        _viewModel = StateObject(wrappedValue: viewModel)
    }

    public var body: some View {
        VStack(spacing: 0) {
            // Header Bar
            headerView

            Divider()

            // Chat Scroll
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(alignment: .leading, spacing: 16) {
                        ForEach(viewModel.messages) { msg in
                            messageBubble(for: msg)
                                .id(msg.id)
                        }

                        if viewModel.isBusy {
                            typingIndicator
                                .id("busy_indicator")
                        }
                    }
                    .padding()
                }
                .onChange(of: viewModel.messages.count) { _ in
                    withAnimation(.easeOut(duration: 0.25)) {
                        if let last = viewModel.messages.last {
                            proxy.scrollTo(last.id, anchor: .bottom)
                        }
                    }
                }
            }

            // Quick Chips
            quickSuggestionBar

            Divider()

            // Input Bar
            inputBar
        }
        #if os(macOS)
        .frame(minWidth: 480, minHeight: 600)
        #endif
        .background(Color(NSColor.windowBackgroundColor))
    }

    // MARK: - Subviews

    private var headerView: some View {
        HStack(spacing: 12) {
            ZStack {
                Circle()
                    .fill(
                        LinearGradient(
                            colors: [Color.cyan, Color.blue],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .frame(width: 32, height: 32)
                Text("🧬")
                    .font(.system(size: 16))
            }

            VStack(alignment: .leading, spacing: 2) {
                HStack(spacing: 6) {
                    Text("SYNAX Code AI")
                        .font(.headline)
                        .fontWeight(.bold)
                    Text("v0.7.0")
                        .font(.caption2)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(Color.blue.opacity(0.15))
                        .foregroundColor(.blue)
                        .clipShape(Capsule())
                }

                HStack(spacing: 4) {
                    Circle()
                        .fill(viewModel.isConnected ? Color.green : Color.orange)
                        .frame(width: 8, height: 8)
                    Text(viewModel.isConnected ? "Çalışma Zamanı Hazır (NEON SIMD)" : "Bağlantı Kuruluyor...")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }

            Spacer()

            Menu {
                Button("🧠 Hafıza & Beceriler") {
                    viewModel.sendMessage("hafızanı göster")
                }
                Button("⚡ Donanım Durumu") {
                    viewModel.sendMessage("durum")
                }
                Divider()
                Button("🔄 Yeniden Bağlan") {
                    Task { await viewModel.checkConnection() }
                }
            } label: {
                Image(systemName: "ellipsis.circle")
                    .font(.title3)
                    .foregroundColor(.secondary)
            }
            .menuStyle(.borderlessButton)
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
    }

    private func messageBubble(for msg: SynaxChatMessage) -> some View {
        HStack(alignment: .top, spacing: 12) {
            if !msg.isUser {
                Image(systemName: "cpu")
                    .font(.system(size: 14))
                    .foregroundColor(.white)
                    .frame(width: 28, height: 28)
                    .background(Color.blue)
                    .clipShape(Circle())
            } else {
                Spacer(minLength: 40)
            }

            VStack(alignment: msg.isUser ? .trailing : .leading, spacing: 8) {
                // Metin Gövdesi
                Text(LocalizedStringKey(msg.text))
                    .font(.system(size: 14))
                    .foregroundColor(msg.isUser ? .white : .primary)
                    .padding(.horizontal, 14)
                    .padding(.vertical, 10)
                    .background(
                        msg.isUser
                            ? Color.blue
                            : Color(NSColor.controlBackgroundColor)
                    )
                    .cornerRadius(12)

                // Varsa Kod Bloğu
                if let code = msg.code, !code.isEmpty {
                    codeBlockView(code: code, language: msg.language ?? "synax")
                }
            }

            if msg.isUser {
                Image(systemName: "person.crop.circle.fill")
                    .font(.system(size: 24))
                    .foregroundColor(.secondary)
            } else {
                Spacer(minLength: 40)
            }
        }
    }

    private func codeBlockView(code: String, language: String) -> some View {
        VStack(alignment: .leading, spacing: 0) {
            // Header bar
            HStack {
                Text(language.uppercased())
                    .font(.caption2)
                    .fontWeight(.bold)
                    .foregroundColor(.cyan)
                Spacer()

                Button {
                    #if os(macOS)
                    NSPasteboard.general.clearContents()
                    NSPasteboard.general.setString(code, forType: .string)
                    #endif
                } label: {
                    Label("Kopyala", systemImage: "doc.on.doc")
                        .font(.caption2)
                }
                .buttonStyle(.borderless)

                if language.lowercased() == "synax" || code.contains("kernel") {
                    Button {
                        viewModel.evolveKernel(code)
                    } label: {
                        Label("Evrimi Yarıştır", systemImage: "bolt.fill")
                            .font(.caption2)
                            .foregroundColor(.orange)
                    }
                    .buttonStyle(.borderless)
                }
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 6)
            .background(Color.black.opacity(0.3))

            // Code Content
            ScrollView(.horizontal, showsIndicators: false) {
                Text(code)
                    .font(.system(.caption, design: .monospaced))
                    .foregroundColor(Color.green.opacity(0.9))
                    .padding(12)
            }
        }
        .background(Color(red: 0.1, green: 0.12, blue: 0.15))
        .cornerRadius(8)
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(Color.white.opacity(0.1), lineWidth: 1)
        )
    }

    private var typingIndicator: some View {
        HStack(spacing: 8) {
            ProgressView()
                .controlSize(.small)
            Text("SYNAX düşünüyor ve optimize ediyor...")
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 8)
        .background(Color(NSColor.controlBackgroundColor).opacity(0.6))
        .cornerRadius(10)
    }

    private var quickSuggestionBar: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                chipButton("🩺 Serebral Perfüzyon (CPP)") {
                    viewModel.sendMessage("Serebral perfüzyon basıncı için bir koruma kerneli yaz")
                }
                chipButton("⚡ Şok İndeksi (SI)") {
                    viewModel.sendMessage("Şok indeksi kernel kodu yaz")
                }
                chipButton("📱 Xcode Entegrasyonu") {
                    viewModel.sendMessage("Xcode projemle SYNAX'ı nasıl bağlayabilirim?")
                }
                chipButton("🏎️ 4-Varyant Evrim") {
                    viewModel.sendMessage("kernel cerebral_guard(a: tensor<f32>, b: tensor<f32>) -> tensor<f32> { let x = a - b; return x; } kodunu evrimleştir")
                }
            }
            .padding(.horizontal, 14)
            .padding(.vertical, 8)
        }
        .background(Color(NSColor.controlBackgroundColor).opacity(0.4))
    }

    private func chipButton(_ title: String, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Text(title)
                .font(.caption)
                .padding(.horizontal, 10)
                .padding(.vertical, 5)
                .background(Color.blue.opacity(0.1))
                .foregroundColor(.blue)
                .clipShape(Capsule())
        }
        .buttonStyle(.plain)
    }

    private var inputBar: some View {
        HStack(spacing: 10) {
            TextField("SYNAX'a danışın, formül verin veya 'kendine şu beceriyi edin:' deyin...", text: $viewModel.inputText)
                .textFieldStyle(.plain)
                .font(.system(size: 14))
                .padding(10)
                .background(Color(NSColor.controlBackgroundColor))
                .cornerRadius(8)
                .focused($isInputFocused)
                .onSubmit {
                    viewModel.sendMessage()
                }

            Button {
                viewModel.sendMessage()
            } label: {
                Image(systemName: "arrow.up.circle.fill")
                    .font(.system(size: 26))
                    .foregroundColor(viewModel.inputText.isEmpty ? .secondary : .blue)
            }
            .buttonStyle(.plain)
            .disabled(viewModel.inputText.isEmpty || viewModel.isBusy)
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 10)
    }
}

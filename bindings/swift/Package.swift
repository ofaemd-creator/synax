// swift-tools-version: 5.9
// The swift-tools-version declares the minimum version of Swift required to build this package.

import PackageDescription

let package = Package(
    name: "SynaxBridge",
    platforms: [
        .macOS(.v13),
        .iOS(.v16)
    ],
    products: [
        .library(
            name: "SynaxBridge",
            targets: ["SynaxBridge"]
        ),
    ],
    targets: [
        .target(
            name: "SynaxBridge",
            dependencies: [],
            path: "Sources/SynaxBridge"
        ),
    ]
)

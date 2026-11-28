import Foundation
import AppKit

func check(_ value: Bool, _ reason: String) throws {
    if !value { throw NSError(domain: "MouseBranding", code: 1, userInfo: [NSLocalizedDescriptionKey: reason]) }
}

do {
    let arguments = CommandLine.arguments
    try check(arguments.count == 3, "Usage: mouse-644-branding.swift application.app output.json")
    let application = URL(fileURLWithPath: arguments[1]).standardizedFileURL
    let output = URL(fileURLWithPath: arguments[2])
    guard let bundle = Bundle(url: application), let info = bundle.infoDictionary else {
        throw NSError(domain: "MouseBranding", code: 1, userInfo: [NSLocalizedDescriptionKey: "Installed application bundle is missing"])
    }
    let displayed = FileManager.default.displayName(atPath: application.path)
    let localizedDisplay = bundle.object(forInfoDictionaryKey: "CFBundleDisplayName") as? String
    let localizedName = bundle.object(forInfoDictionaryKey: "CFBundleName") as? String
    try check(displayed == "Mouse", "Finder display name is \(displayed), expected Mouse")
    try check(localizedDisplay == "Mouse" && localizedName == "Mouse", "Localized bundle names must both be Mouse")
    try check(application.lastPathComponent == "Mouse Browser.app", "Published updater bundle path changed")
    try check(info["CFBundleExecutable"] as? String == "Mouse Browser", "Published updater executable changed")
    try check(info["CFBundleIdentifier"] as? String == "com.osminog.desktop.preview", "Existing application identity changed")
    try check(info["CFBundleShortVersionString"] as? String == "6.0.45", "Unexpected installed version")
    try check(info["CFBundleDisplayName"] as? String == "Mouse Browser", "Base display name must match the compatibility bundle filename")
    let resources = application.appendingPathComponent("Contents/Resources")
    let languages = try FileManager.default.contentsOfDirectory(atPath: resources.path).filter { $0.hasSuffix(".lproj") }.sorted()
    try check(languages.contains("en.lproj") && languages.contains("ru.lproj"), "English/Russian name localization missing")
    for language in languages {
        let data = try Data(contentsOf: resources.appendingPathComponent(language).appendingPathComponent("InfoPlist.strings"))
        let values = try PropertyListSerialization.propertyList(from: data, options: [], format: nil) as? [String: Any]
        try check(values?["CFBundleName"] as? String == "Mouse" && values?["CFBundleDisplayName"] as? String == "Mouse", "Incorrect name in \(language)")
    }
    let result: [String: Any] = ["ok": true, "application": application.path, "displayName": displayed, "localizedDisplayName": localizedDisplay!, "localizedBundleName": localizedName!, "compatibilityBundleName": application.lastPathComponent, "executable": info["CFBundleExecutable"]!, "appId": bundle.bundleIdentifier!, "version": info["CFBundleShortVersionString"]!, "languages": languages, "verifiedAt": ISO8601DateFormatter().string(from: Date())]
    try JSONSerialization.data(withJSONObject: result, options: [.prettyPrinted, .sortedKeys]).write(to: output, options: .atomic)
    print("MOUSE_644_NATIVE_DISPLAY_NAME_PASS")
} catch {
    fputs("Mouse display-name verification failed: \(error)\n", stderr)
    exit(1)
}

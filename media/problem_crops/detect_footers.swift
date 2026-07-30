import AppKit
import Vision

let path = CommandLine.arguments[1]
guard let image = NSImage(contentsOfFile: path),
      let cgImage = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
    print("ERROR: Could not load image")
    exit(1)
}

let imageHeight = cgImage.height
let semaphore = DispatchSemaphore(value: 0)
var footerTopY: Int? = nil

let request = VNRecognizeTextRequest { request, error in
    guard let observations = request.results as? [VNRecognizedTextObservation] else {
        semaphore.signal()
        return
    }
    for obs in observations {
        if let text = obs.topCandidates(1).first?.string {
            // Check if this text block contains our footer
            if text.contains("END for ") || text.contains("END for") {
                // Get the bounding box (normalized: 0.0 to 1.0)
                let boundingBox = obs.boundingBox
                
                // Vision Y starts from bottom. We want the TOP of this text block.
                let normalizedTopY = boundingBox.maxY
                
                // Convert to actual pixel coordinate from the TOP of the image
                // (Vision's 1.0 = top of image, so we invert it for a standard Top-down crop)
                let pixelYFromTop = Int((1.0 - normalizedTopY) * CGFloat(imageHeight))
                
                footerTopY = pixelYFromTop
                break
            }
        }
    }
    semaphore.signal()
}
request.recognitionLevel = .accurate
request.usesLanguageCorrection = false

let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
try? handler.perform([request])
semaphore.wait()

if let y = footerTopY {
    // Print just the number so you can easily capture it in a bash script
    print(y)
} else {
    print("NOT_FOUND")
    exit(1)
}
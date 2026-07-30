#!/bin/bash

# 1. Compile the Swift detector (only once, before the loop)
if [ ! -f "detect" ]; then
    echo "Compiling Swift detector..."
    swiftc -o detect detect_footer.swift
fi

# 2. Loop through all PNG files in the current folder
for IMAGE_PATH in *.png; do

    # 3. Skip files that already have "_no_footer" in their name
    if [[ "$IMAGE_PATH" == *"_no_footer"* ]]; then
        echo "Skipping already cropped file: $IMAGE_PATH"
        continue
    fi

    # 4. If the file is not skipped, process it
    echo "----------------------------------------"
    echo "Processing: $IMAGE_PATH"
    
    OUTPUT_PATH="${IMAGE_PATH%.*}_no_footer.${IMAGE_PATH##*.}"

    # 5. Get the Y coordinate of the top of the footer
    echo "Scanning for footer text..."
    FOOTER_Y=$(./detect "$IMAGE_PATH")

    if [ "$FOOTER_Y" == "NOT_FOUND" ]; then
        echo "⚠️ Warning: Footer text not found in $IMAGE_PATH. Skipping."
        continue
    fi

    echo "Footer detected starting at pixel Y: $FOOTER_Y"

    # 6. Apply a 10-pixel safety margin
    CROP_HEIGHT=$((FOOTER_Y - 10))
    echo "Applying -10px safety margin. New crop height: $CROP_HEIGHT"

    # 7. Crop using ImageMagick
    magick "$IMAGE_PATH" -crop "x${CROP_HEIGHT}+0+0" "$OUTPUT_PATH"

    echo "✅ Saved to: $OUTPUT_PATH"
done

echo "----------------------------------------"
echo "All done!"
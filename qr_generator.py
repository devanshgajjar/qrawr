import qrcode
import sys
from pathlib import Path
import re

def sanitize_filename(filename):
    """Sanitize the filename by removing invalid characters"""
    # Remove invalid filename characters and replace spaces with underscores
    sanitized = re.sub(r'[<>:"/\\|?*]', '', filename)
    return sanitized.replace(' ', '_')

def generate_qr(link, output_file=None):
    """Generate a QR code from a link and save it to a file"""
    try:
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(link)
        qr.make(fit=True)

        # Create QR image
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Generate output filename if not provided
        if not output_file:
            # Extract domain from link for filename
            filename = link.split('//')[1].split('/')[0] if '//' in link else link
            filename = sanitize_filename(filename)
            output_file = f"qr_{filename}.png"

        # Ensure the filename ends with .png
        if not output_file.lower().endswith('.png'):
            output_file += '.png'

        # Save the image
        qr_image.save(output_file)
        return True, output_file
    except Exception as e:
        return False, str(e)

def main():
    # Check if link is provided as command line argument
    if len(sys.argv) > 1:
        link = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
    else:
        # If no command line argument, ask for input
        link = input("Enter the link to generate a QR code: ").strip()
        output_file = input("Enter output filename (optional, press Enter for auto-generated name): ").strip()
        output_file = output_file if output_file else None

    # Generate QR code
    success, result = generate_qr(link, output_file)
    
    if success:
        print(f"QR code successfully generated and saved as '{result}'")
    else:
        print(f"Error generating QR code: {result}")

if __name__ == "__main__":
    main() 
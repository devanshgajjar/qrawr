from flask import Flask, request, render_template
import qrcode
import qrcode.image.svg
from io import BytesIO
import base64
from PIL import Image, ImageDraw

app = Flask(__name__)

class QRCodeGenerator:
    def __init__(self):
        self.box_size = 10
        self.border = 4

    def generate_qr(self, data, dot_style="square", marker_style="square", marker_center="square", fg_color="#000000", bg_color="#FFFFFF"):
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=self.box_size,
                border=self.border,
            )
            qr.add_data(data)
            qr.make(fit=True)

            # Calculate dimensions
            size = (qr.modules_count + 2 * self.border) * self.box_size
            
            # Start SVG content
            svg_content = [
                '<?xml version="1.0" encoding="UTF-8"?>',
                f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" width="{size}" height="{size}">',
            ]

            # Add background if not transparent
            if bg_color and bg_color != "transparent":
                svg_content.append(f'<rect width="{size}" height="{size}" fill="{bg_color}"/>')

            # Start QR code group
            svg_content.append(f'<g fill="{fg_color}">')

            # Draw QR code modules
            for row in range(qr.modules_count):
                for col in range(qr.modules_count):
                    if qr.modules[row][col]:
                        x = (col + self.border) * self.box_size
                        y = (row + self.border) * self.box_size

                        is_marker = (row < 7 and col < 7) or \
                                   (row < 7 and col >= qr.modules_count - 7) or \
                                   (row >= qr.modules_count - 7 and col < 7)

                        if not is_marker:
                            if dot_style == "rounded":
                                # Check adjacent dots
                                has_right = col + 1 < qr.modules_count and qr.modules[row][col + 1]
                                has_bottom = row + 1 < qr.modules_count and qr.modules[row + 1][col]
                                has_left = col - 1 >= 0 and qr.modules[row][col - 1]
                                has_top = row - 1 >= 0 and qr.modules[row - 1][col]

                                # Create path for rounded rectangle with selective rounding
                                path = [
                                    f'M {x + (0 if has_left else self.box_size/4)} {y}',  # Start from left
                                    f'H {x + self.box_size - (0 if has_right else self.box_size/4)}',  # Top line
                                    f'Q {x + self.box_size} {y} {x + self.box_size} {y + (0 if has_right else self.box_size/4)}',  # Top-right corner
                                    f'V {y + self.box_size - (0 if has_bottom else self.box_size/4)}',  # Right line
                                    f'Q {x + self.box_size} {y + self.box_size} {x + self.box_size - (0 if has_bottom else self.box_size/4)} {y + self.box_size}',  # Bottom-right corner
                                    f'H {x + (0 if has_left else self.box_size/4)}',  # Bottom line
                                    f'Q {x} {y + self.box_size} {x} {y + self.box_size - (0 if has_left else self.box_size/4)}',  # Bottom-left corner
                                    f'V {y + (0 if has_top else self.box_size/4)}',  # Left line
                                    f'Q {x} {y} {x + (0 if has_top else self.box_size/4)} {y}',  # Top-left corner
                                    'Z'  # Close path
                                ]
                                svg_content.append(f'<path d="{" ".join(path)}"/>')
                            elif dot_style == "square":
                                svg_content.append(f'<rect x="{x}" y="{y}" width="{self.box_size}" height="{self.box_size}"/>')
                            elif dot_style == "circle":
                                cx = x + self.box_size/2
                                cy = y + self.box_size/2
                                r = self.box_size/2 * 0.95
                                svg_content.append(f'<circle cx="{cx}" cy="{cy}" r="{r}"/>')

            # Draw position detection patterns
            for pos in [(0, 0), (0, qr.modules_count - 7), (qr.modules_count - 7, 0)]:
                x = (pos[1] + self.border) * self.box_size
                y = (pos[0] + self.border) * self.box_size
                outer_size = self.box_size * 7
                inner_size = self.box_size * 5
                center_size = self.box_size * 3

                # Outer border
                if marker_style == "square":
                    svg_content.append(f'<rect x="{x}" y="{y}" width="{outer_size}" height="{outer_size}"/>')
                elif marker_style == "rounded":
                    svg_content.append(f'<rect x="{x}" y="{y}" width="{outer_size}" height="{outer_size}" rx="{self.box_size}"/>')
                elif marker_style == "circle":
                    cx = x + outer_size/2
                    cy = y + outer_size/2
                    svg_content.append(f'<circle cx="{cx}" cy="{cy}" r="{outer_size/2}"/>')

                # White space
                inner_x = x + self.box_size
                inner_y = y + self.box_size
                svg_content.append(f'<rect x="{inner_x}" y="{inner_y}" width="{inner_size}" height="{inner_size}" fill="white"/>')

                # Center marker
                center_x = x + (outer_size - center_size)/2
                center_y = y + (outer_size - center_size)/2
                if marker_center == "square":
                    svg_content.append(f'<rect x="{center_x}" y="{center_y}" width="{center_size}" height="{center_size}"/>')
                elif marker_center == "dot":
                    cx = center_x + center_size/2
                    cy = center_y + center_size/2
                    r = center_size/2 * 0.6
                    svg_content.append(f'<circle cx="{cx}" cy="{cy}" r="{r}"/>')

            # Close SVG
            svg_content.append('</g>')
            svg_content.append('</svg>')

            return True, '\n'.join(svg_content)
        except Exception as e:
            print(f"Error generating QR code: {str(e)}")
            return False, str(e)

    def generate_png(self, data, dot_style="square", marker_style="square", marker_center="square", fg_color="#000000", bg_color="#FFFFFF"):
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=self.box_size,
                border=self.border,
            )
            qr.add_data(data)
            qr.make(fit=True)

            # Calculate dimensions
            size = (qr.modules_count + 2 * self.border) * self.box_size

            # Create image with alpha channel for transparency
            if bg_color == "transparent" or bg_color is None:
                img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            else:
                img = Image.new('RGB', (size, size), bg_color)

            draw = ImageDraw.Draw(img)

            # Convert color string to RGB
            if isinstance(fg_color, str) and fg_color.startswith('#'):
                fg_color = tuple(int(fg_color[i:i+2], 16) for i in (1, 3, 5))

            # Draw QR code modules
            for row in range(qr.modules_count):
                for col in range(qr.modules_count):
                    if qr.modules[row][col]:
                        x = (col + self.border) * self.box_size
                        y = (row + self.border) * self.box_size

                        is_marker = (row < 7 and col < 7) or \
                                   (row < 7 and col >= qr.modules_count - 7) or \
                                   (row >= qr.modules_count - 7 and col < 7)

                        if not is_marker:
                            if dot_style == "rounded":
                                # Check adjacent dots
                                has_right = col + 1 < qr.modules_count and qr.modules[row][col + 1]
                                has_bottom = row + 1 < qr.modules_count and qr.modules[row + 1][col]
                                has_left = col - 1 >= 0 and qr.modules[row][col - 1]
                                has_top = row - 1 >= 0 and qr.modules[row - 1][col]

                                # Draw the base rectangle
                                draw.rectangle([x, y, x + self.box_size, y + self.box_size], fill=fg_color)

                                # Draw corner arcs where needed (where there's no adjacent dot)
                                radius = self.box_size/4
                                if not has_top and not has_left:
                                    draw.pieslice([x, y, x + radius*2, y + radius*2], 180, 270, fill=bg_color or (0,0,0,0))
                                if not has_top and not has_right:
                                    draw.pieslice([x + self.box_size - radius*2, y, x + self.box_size, y + radius*2], 270, 0, fill=bg_color or (0,0,0,0))
                                if not has_bottom and not has_right:
                                    draw.pieslice([x + self.box_size - radius*2, y + self.box_size - radius*2, x + self.box_size, y + self.box_size], 0, 90, fill=bg_color or (0,0,0,0))
                                if not has_bottom and not has_left:
                                    draw.pieslice([x, y + self.box_size - radius*2, x + radius*2, y + self.box_size], 90, 180, fill=bg_color or (0,0,0,0))
                            elif dot_style == "square":
                                draw.rectangle([x, y, x + self.box_size, y + self.box_size], fill=fg_color)
                            elif dot_style == "circle":
                                padding = self.box_size * 0.05
                                draw.ellipse([x + padding, y + padding, 
                                             x + self.box_size - padding, 
                                             y + self.box_size - padding], 
                                           fill=fg_color)

            # Draw position detection patterns
            for pos in [(0, 0), (0, qr.modules_count - 7), (qr.modules_count - 7, 0)]:
                x = (pos[1] + self.border) * self.box_size
                y = (pos[0] + self.border) * self.box_size
                outer_size = self.box_size * 7
                inner_size = self.box_size * 5
                center_size = self.box_size * 3

                # Outer border
                if marker_style == "square":
                    draw.rectangle([x, y, x + outer_size, y + outer_size], fill=fg_color)
                elif marker_style == "rounded":
                    draw.rounded_rectangle([x, y, x + outer_size, y + outer_size], 
                                        radius=self.box_size, fill=fg_color)
                elif marker_style == "circle":
                    draw.ellipse([x, y, x + outer_size, y + outer_size], fill=fg_color)

                # White space
                draw.rectangle([x + self.box_size, y + self.box_size, 
                              x + outer_size - self.box_size, y + outer_size - self.box_size], 
                               fill='white')

                # Center marker
                center_x = x + (outer_size - center_size)/2
                center_y = y + (outer_size - center_size)/2
                if marker_center == "square":
                    draw.rectangle([center_x, center_y, center_x + center_size, center_y + center_size], 
                                 fill=fg_color)
                elif marker_center == "dot":
                    padding = center_size * 0.2
                    dot_size = center_size * 0.6
                    center_x = x + (outer_size - dot_size)/2
                    center_y = y + (outer_size - dot_size)/2
                    draw.ellipse([
                        center_x,
                        center_y,
                        center_x + dot_size,
                        center_y + dot_size
                    ], fill=fg_color)

            # Convert to bytes
            img_byte_arr = BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            return True, img_byte_arr.getvalue()

        except Exception as e:
            print(f"Error generating PNG: {str(e)}")
            return False, str(e)

qr_generator = QRCodeGenerator()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.json
        link = data.get('link', '')
        dot_style = data.get('dotStyle', 'square')
        marker_style = data.get('markerStyle', 'square')
        marker_center = data.get('markerCenter', 'square')
        fg_color = data.get('fgColor', '#000000')
        bg_color = data.get('bgColor', '#FFFFFF')
        format = data.get('format', 'svg')  # Default to SVG
        
        if not link:
            return {'success': False, 'error': 'No link provided'}, 400
            
        if format == 'png':
            success, result = qr_generator.generate_png(
                link,
                dot_style=dot_style,
                marker_style=marker_style,
                marker_center=marker_center,
                fg_color=fg_color,
                bg_color=bg_color if bg_color != 'transparent' else None
            )
            if success:
                encoded = base64.b64encode(result).decode('utf-8')
                return {
                    'success': True,
                    'image': f'data:image/png;base64,{encoded}'
                }
        else:
            success, result = qr_generator.generate_qr(
                link,
                dot_style=dot_style,
                marker_style=marker_style,
                marker_center=marker_center,
                fg_color=fg_color,
                bg_color=bg_color if bg_color != 'transparent' else None
            )
            if success:
                return {
                    'success': True,
                    'svg': result
                }
                
        return {'success': False, 'error': result}, 500
        
    except Exception as e:
        print(f"Request error: {str(e)}")
        return {'success': False, 'error': str(e)}, 500

if __name__ == '__main__':
    app.run(debug=True, port=5001) 
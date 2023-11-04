from PIL import Image, ImageDraw, ImageFont
import os

class SignEditor:
    def __init__(self, output_file_location="images", font_path="arial.ttf", font_size=80, fill="black", x=140, y=130, output_image_name="modified_image.jpg"):
        self.font_size = font_size
        self.font_path = font_path
        self.fill = fill
        self.x = x
        self.y = y
        self.output_file_location = output_file_location
        self.output_image_name = output_image_name

    def add_text_to_image(self, image_path, text):
        # Open the image
        try:
            with Image.open(image_path) as img:

                # Set up the drawing context
                draw = ImageDraw.Draw(img)

                # Ensure the output directory exists
                if not os.path.exists(self.output_file_location):
                    os.makedirs(self.output_file_location)

                # Draw the text on the image
                draw.text((self.x, self.y), str(text), font=ImageFont.truetype(self.font_path, self.font_size), fill=self.fill)
                
                # Save the modified image
                output_path = os.path.join(self.output_file_location, self.output_image_name)
                img.save(output_path)
                
                print(f"Image saved to {output_path}")
        except Exception as e:
            print(f"An error occurred: {e}")
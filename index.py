import os
import shutil
import zipfile
from PIL import Image

class WhatsAppStickerPackCreator:
    def __init__(self, folder_name):
        self.folder_name = folder_name

    def create_sticker_pack(self):
        #Check if folder exists
        input_folder = os.path.join(os.getcwd(), self.folder_name)
        if not os.path.isdir(input_folder):
            print(f"Error: Folder '{self.folder_name}' not found in the current directory.")
            return

        #Create a new folder to hold everything
        sticker_pack_name = input_folder + "_webp"  # Replace with your desired name
        output_folder = os.path.join(os.getcwd(), sticker_pack_name)
        os.makedirs(output_folder, exist_ok=True)

        #Move original images folder into new folder
        new_input_folder = os.path.join(output_folder, self.folder_name)
        shutil.move(input_folder, new_input_folder)

        #Create processed images folder
        processed_images_folder = os.path.join(output_folder, "processed_images")
        os.makedirs(processed_images_folder, exist_ok=True)

        #Process images and GIFs, and select first image as tray icon
        image_processor = ImageProcessor()
        first_image_processed = False
        for file in os.listdir(new_input_folder):
            if file.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                file_path = os.path.join(new_input_folder, file)
                image_processor.process_image_or_gif(file_path, processed_images_folder)

                if not first_image_processed:
                    # Resize first image to 96x96 for the tray icon
                    tray_image_path = os.path.join(processed_images_folder, os.path.basename(file_path)[:-4] + ".webp")
                    image_processor.resize_for_tray_icon(tray_image_path)
                    first_image_processed = True

        #Create contents.json (use the selected tray_image_path)
        json_generator = JsonMetadataGenerator()
        json_generator.create_contents_json(processed_images_folder, output_folder, tray_image_path)

        #Create the .wastickers ZIP archive
        archiver = StickerPackArchiver()
        archiver.create_sticker_pack_archive(output_folder, sticker_pack_name, tray_image_path)

class ImageProcessor:
    def process_image_or_gif(self, file_path, output_folder):
        try:
            if file_path.endswith('.gif'):
                # Handle GIFs
                img = Image.open(file_path)
                frames = []
                for frame_index in range(img.n_frames):
                    img.seek(frame_index)
                    frame = img.convert('RGBA')

                    width, height = frame.size
                    if width > height:
                        new_width = 512
                        new_height = int(height * (512 / width))
                    else:
                        new_height = 512
                        new_width = int(width * (512 / height))
                    frame = frame.resize((new_width, new_height), Image.LANCZOS)

                    final_frame = Image.new('RGBA', (512, 512), (0, 0, 0, 0))
                    final_frame.paste(frame, ((512 - new_width) // 2, (512 - new_height) // 2))
                    frames.append(final_frame)

                output_path = os.path.join(output_folder, os.path.basename(file_path)[:-4] + ".webp")
                frames[0].save(output_path, "webp", save_all=True, append_images=frames[1:], lossless=True, disposal=2, loop=0)

            else:
                # Handle other image formats
                img = Image.open(file_path).convert('RGBA')

                width, height = img.size
                if width > height:
                    new_width = 512
                    new_height = int(height * (512 / width))
                else:
                    new_height = 512
                    new_width = int(width * (512 / height))
                img = img.resize((new_width, new_height), Image.LANCZOS)

                final_image = Image.new('RGBA', (512, 512), (0, 0, 0, 0))
                final_image.paste(img, ((512 - new_width) // 2, (512 - new_height) // 2))

                output_path = os.path.join(output_folder, os.path.basename(file_path)[:-4] + ".webp")
                final_image.save(output_path, "webp", lossless=True)

            print(f"Processed: {file_path} -> {output_path}")

        except Exception as e:
            print(f"Error processing {file_path}: {e}")

    def resize_for_tray_icon(self, image_path):
        try:
            img = Image.open(image_path).convert('RGBA')
            img = img.resize((96, 96), Image.LANCZOS)
            img.save(image_path, "webp", lossless=True)
            print(f"Resized for tray icon: {image_path}")
        except Exception as e:
            print(f"Error resizing for tray icon: {e}")

class JsonMetadataGenerator:
    def create_contents_json(self, image_folder, output_folder, tray_image_path):
        sticker_data = []

        image_files = [f for f in os.listdir(image_folder) if f.endswith('.webp')]

        for image_file in image_files:
            sticker_data.append({
                "image_file": image_file,
                "emojis": []  # You'll need to add logic to assign emojis if needed
            })

        contents = {
            "identifier": "unique_sticker_pack_id",
            "name": output_folder,
            "publisher": "Sticker_Packer",
            "tray_image": os.path.basename(tray_image_path),
            "version": 1,
            "stickers": sticker_data
        }

        json_file_path = os.path.join(output_folder, "contents.json")
        with open(json_file_path, "w") as f:
            json.dump(contents, f, indent=2)

        print(f"contents.json created in {output_folder}")

class StickerPackArchiver:
    def create_sticker_pack_archive(self, output_folder, sticker_pack_name, tray_image_path):
        zip_file_path = os.path.join(output_folder, f"{sticker_pack_name}.wastickers")
        with zipfile.ZipFile(zip_file_path, 'w') as zipf:
            for file in os.listdir(output_folder):
                if file.endswith('.webp') or file == "contents.json" or file == os.path.basename(tray_image_path):
                    file_path = os.path.join(output_folder, file)
                    zipf.write(file_path, arcname=file)

        print(f"Sticker pack created: {zip_file_path}")

if __name__ == "__main__":
    folder_name = input("Enter the Image Folder name (in the current directory): ")

    creator = WhatsAppStickerPackCreator(folder_name)
    creator.create_sticker_pack()
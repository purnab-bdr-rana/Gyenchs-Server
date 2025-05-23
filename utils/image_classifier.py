import os
import numpy as np
import tensorflow as tf
from PIL import Image, UnidentifiedImageError
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
import tempfile
import time

class ImageClassifier:
    def __init__(self, model_path="mobilenetv2_optimized.tflite"):
        # Automatically resolve absolute path relative to project root
        if not os.path.isabs(model_path):
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            model_path = os.path.join(base_dir, model_path)

        self.interpreter = tf.lite.Interpreter(model_path=model_path)
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        self.class_labels = {0: 'kira', 1: 'tego', 2: 'unknown', 3: 'wonju'}

    def predict_type(self, image_file):
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp:
                image_file.save(temp.name)
                img = Image.open(temp.name).resize((224, 224))
                img = np.array(img).astype(np.float32)
                img = preprocess_input(img)
                img = np.expand_dims(img, axis=0)

                self.interpreter.set_tensor(self.input_details[0]['index'], img)

                start_time = time.time()
                self.interpreter.invoke()
                end_time = time.time()

                output = self.interpreter.get_tensor(self.output_details[0]['index'])[0]
                predicted_index = np.argmax(output)
                confidence = output[predicted_index]

                if confidence < 0.6:
                    raise ValueError("Invalid image. Upload either kira, tego or wonju.")
                
                if self.class_labels[predicted_index] == 'unknown':
                    raise ValueError("Invalid image. Upload either kira, tego or wonju.")


                print(f"Time taken for request: {end_time - start_time:.3f} seconds")
                return self.class_labels[predicted_index]
        except UnidentifiedImageError:
            raise ValueError("Uploaded image file is not a valid image.")

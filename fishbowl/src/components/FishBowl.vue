<style scoped>
</style><template>
  <div class="container">
    <div class="content">
      <h1>Water Level Detector</h1>
      <label class="upload-label">
        <div class="upload-text">
          {{ image ? "Upload New Image" : "Upload Image" }}
        </div>
        <input type="file" accept="image/*" @change="handleImageUpload" />
      </label>
      <div v-if="image" class="image-container">
        <div class="image-wrapper">
          <img :src="image" alt="Uploaded Preview" />
        </div>
      </div>
      <p v-if="waterLevel !== null" class="water-level">Water Level: {{ waterLevel }}%</p>
      <p v-if="waterLevel !== null" class="feedback-message">{{ getFeedbackMessage() }}</p>
      <p v-if="error" class="error-message">{{ error }}</p>
    </div>
  </div>
</template>

<script>
import { ref } from "vue";
import goldfish from "@/assets/goldfish.png";
import UploadIcon from "@/components/UploadIcon.vue";
import { motion } from "framer-motion";

export default {
  setup() {
    const image = ref(null);
    const waterLevel = ref(null);
    const error = ref(null);

    const handleImageUpload = (event) => {
      const file = event.target.files[0];
      if (file) {
        image.value = URL.createObjectURL(file);
        processImage(file);
      }
    };

    const processImage = async (file) => {
      const formData = new FormData();
      formData.append("file", file);
      try {
        const response = await fetch("http://localhost:5000/predict", {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          throw new Error(`Server error: ${response.statusText}`);
        }

        const data = await response.json();
        if (!data || typeof data.water_level === "undefined" || typeof data.image === "undefined") {
          throw new Error("Invalid response from server");
        }

        const byteArray = new Uint8Array(data.image.match(/.{1,2}/g).map(byte => parseInt(byte, 16)));
        const blob = new Blob([byteArray], { type: "image/jpeg" });
        const imageUrl = URL.createObjectURL(blob);

        image.value = imageUrl;
        waterLevel.value = Math.floor(data.water_level * 100);
        error.value = null;
      } catch (err) {
        console.error("Error processing image", err);
        error.value = "Error detecting water level. Please ensure the server is running and CORS is configured correctly.";
      }
    };

    const getFeedbackMessage = () => {
      if (waterLevel.value === null) return "";
      if (waterLevel.value < 20) return "Your goldfish died";
      if (waterLevel.value < 50) return "Your goldfish very thirsty";
      if (waterLevel.value < 70) return "Your goldfish needs more water";
      if (waterLevel.value < 90) return "Your goldfish is happy!";
      return "Your goldfish can escape!";
    };

    const getFishAnimation = () => {
      return {
        y: waterLevel.value !== null && waterLevel.value < 75 ? [0, 50] : [0, -10, 0],
        rotate: waterLevel.value !== null && waterLevel.value < 20 ? 180 : 0,
      };
    };

    return {
      image,
      motion,
      waterLevel,
      error,
      handleImageUpload,
      getFeedbackMessage,
      getFishAnimation,
      UploadIcon,
      goldfish,
    };
  },
};
</script>

<style scoped>
.container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background-color: white;
  padding: 24px;
  color: black;
}

.content {
  max-width: 384px;
  width: 100%;
  background-color: #f3f4f6;
  box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1);
  border-radius: 24px;
  padding: 24px;
  text-align: center;
  border: 1px solid #e5e7eb;
}

h1 {
  font-size: 1.5rem;
  font-weight: 600;
  color: black;
  margin-bottom: 16px;
}

.upload-label {
  cursor: pointer;
  background-color: #e4e4e4;
  color: black;
  padding: 12px 24px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  transition: background-color 0.2s;
}

.upload-label:hover {
  background-color: #b4b4b4;
}

input[type="file"] {
  display: none;
}

.image-container {
  margin-top: 24px;
  display: flex;
  justify-content: center;
}

.image-wrapper {
  width: 256px;
  height: 256px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #e5e7eb;
  border-radius: 50%;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
  opacity: 1.0;
}

.water-level {
  margin-top: 16px;
  font-weight: 500;
}

.feedback-message {
  margin-top: 8px;
  font-weight: 600;
}

.error-message {
  margin-top: 16px;
  color: #f87171;
  font-weight: 500;
}
</style>

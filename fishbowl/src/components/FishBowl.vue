<template>
  <div class="flex flex-col items-center justify-center min-h-screen bg-white p-6 text-black">
    <div class="max-w-md w-full bg-gray-100 shadow-lg rounded-3xl p-6 text-center border border-gray-300">
      <h1 class="text-2xl font-semibold text-black mb-4">Water Level Detector</h1>
      <label class="cursor-pointer bg-gray-300 text-black py-3 px-6 rounded-xl flex items-center justify-center gap-2 shadow-md hover:bg-gray-400 transition">
        <UploadIcon /> {{ image ? "Upload New Image" : "Upload Image" }}
        <input type="file" accept="image/*" class="hidden" @change="handleImageUpload" />
      </label>
      <div v-if="image" class="mt-6 relative flex justify-center">
        <div class="relative w-72 h-72 flex items-center justify-center bg-gray-200 rounded-full shadow-inner overflow-hidden">
          <img :src="image" alt="Uploaded Preview" class="absolute w-64 h-64 object-cover rounded-full opacity-50" />
          <!---
          <motion-img
            :src="goldfish"
            alt="Goldfish"
            class="w-20 h-20"
            :animate="getFishAnimation()"
            transition="{ repeat: Infinity, duration: 2 }"
          />
          -->
        </div>
      </div>
      <p v-if="waterLevel !== null" class="mt-4 text-black font-medium">Water Level: {{ waterLevel }}%</p>
      <p v-if="waterLevel !== null" class="mt-2 text-black font-semibold">{{ getFeedbackMessage() }}</p>
      <p v-if="error" class="mt-4 text-red-500 font-medium">{{ error }}</p>
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
          /*
        const response = await fetch("http://localhost:5000/predict", {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          throw new Error(`Server error: ${response.statusText}`);
        }

        const data = await response.json();
        if (!data || typeof data.water_level === "undefined") {
          throw new Error("Invalid response from server");
        }
        waterLevel.value = data.water_level;
        */
        waterLevel.value = Math.floor(Math.random() * 100);
        error.value = null;
      } catch (err) {
        console.error("Error processing image", err);
        error.value = "Error detecting water level. Please ensure the server is running and CORS is configured correctly.";
      }
    };

    const getFeedbackMessage = () => {
      if (waterLevel.value === null) return "";
      if (waterLevel.value < 20) return "Goldie died";
      if (waterLevel.value < 50) return "Goldie is very thirsty";
      if (waterLevel.value < 70) return "Goldie needs more water";
      return "Goldie is happy!";
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
input[type="file"] {
  display: none;
}
</style>

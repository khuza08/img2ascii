<script setup lang="ts">
import { ref, onMounted, watch } from "vue";
import { invoke } from "@tauri-apps/api/core";
import { open } from "@tauri-apps/plugin-dialog";
import { getCurrentWindow } from "@tauri-apps/api/window";
import { openPath } from "@tauri-apps/plugin-opener";
import { 
  FolderOpen, 
  Maximize, 
  Sun, 
  Contrast, 
  Droplet, 
  RefreshCw, 
  ExternalLink 
} from "lucide-vue-next";

interface ConversionResult {
  image_path: string;
  image_base64: string;
  txt_path: string;
}

const filepath = ref("");
const filename = ref("No image selected");
const outputName = ref("ascii_output");
const scaleFactor = ref(0.1);
const brightness = ref(1.0);
const contrast = ref(1.0);
const saturation = ref(1.0);
const isConverting = ref(false);

const resultImagePath = ref("");
const displayImagePath = ref("");

function getSliderStyle(value: number, min: number, max: number) {
  const percentage = ((value - min) / (max - min)) * 100;
  return {
    background: `linear-gradient(to right, #e5e5e5 ${percentage}%, #262626 ${percentage}%)`
  };
}

async function convert() {
  if (!filepath.value) return;
  
  isConverting.value = true;
  try {
    const result = await invoke<ConversionResult>("convert_image", {
      params: {
        filepath: filepath.value,
        output_name: outputName.value,
        scale_factor: scaleFactor.value,
        brightness: brightness.value,
        contrast: contrast.value,
        saturation: saturation.value
      }
    });
    
    resultImagePath.value = result.image_path;
    displayImagePath.value = result.image_base64;
  } catch (error) {
    console.error(error);
  } finally {
    isConverting.value = false;
  }
}

async function openResultImage() {
  if (resultImagePath.value) {
    try {
      await openPath(resultImagePath.value);
    } catch (error) {
      console.error("Failed to open image:", error);
    }
  }
}

watch(filepath, () => {
  if (filepath.value) {
    convert();
  }
});

async function selectImage() {
  const selected = await open({
    multiple: false,
    filters: [{
      name: 'Image',
      extensions: ['png', 'jpg', 'jpeg', 'bmp', 'gif']
    }]
  });
  if (selected && !Array.isArray(selected)) {
    filepath.value = selected;
    filename.value = selected.split(/[/\\]/).pop() || selected;
  }
}

onMounted(async () => {
  (getCurrentWindow() as any).onDragDropEvent((event: any) => {
    if (event.payload.type === 'drop') {
      const droppedPath = event.payload.paths[0];
      if (droppedPath) {
        filepath.value = droppedPath;
        filename.value = droppedPath.split(/[/\\]/).pop() || droppedPath;
      }
    }
  });

  await getCurrentWindow().show();
});
</script>

<template>
  <div class="flex flex-col lg:flex-row h-screen w-screen p-2 lg:p-3 gap-2 lg:gap-3 bg-black box-border overflow-y-auto lg:overflow-hidden font-sans">
    <!-- Sidebar -->
    <aside class="w-full lg:w-80 glass-panel p-6 flex flex-col gap-5 shrink-0 rounded-[20px] lg:rounded-[28px] overflow-y-visible lg:overflow-y-auto">
      <div class="logo-section flex items-center gap-3">
        <div class="w-10 h-10 bg-neutral-200 rounded-xl flex items-center justify-center text-black shrink-0">
          <RefreshCw :size="20" :class="{ 'animate-spin': isConverting }" />
        </div>
        <div>
          <h1 class="m-0 text-xl font-extrabold tracking-tighter text-neutral-200">img2ascii</h1>
          <p class="text-[10px] text-neutral-500 uppercase tracking-widest font-bold">by khuza08</p>
        </div>
      </div>

      <div class="flex flex-col gap-2">
        <label class="text-[10px] uppercase tracking-widest text-neutral-500 font-bold">Source Image</label>
        <div 
          class="bg-neutral-900 border border-neutral-800 rounded-full py-2.5 px-5 flex items-center gap-3 cursor-pointer transition-all duration-300 hover:border-neutral-700 hover:bg-neutral-800/50 group"
          @click="selectImage"
        >
          <FolderOpen :size="18" class="text-neutral-500 group-hover:text-white transition-colors" />
          <div class="flex flex-col overflow-hidden">
            <span class="text-xs text-neutral-300 truncate font-medium">{{ filename }}</span>
          </div>
        </div>
      </div>

      <div class="flex flex-col gap-2">
        <label class="text-[10px] uppercase tracking-widest text-neutral-500 font-bold">Output Filename</label>
        <input 
          v-model="outputName" 
          placeholder="filename" 
          class="bg-neutral-900 border border-neutral-800 rounded-full py-2.5 px-5 text-white text-xs outline-none transition-all focus:border-neutral-700 focus:bg-neutral-800/50" 
        />
      </div>

      <div class="flex flex-col gap-5 py-6 bg-neutral-900 rounded-xl px-4">
        <div class="flex flex-col gap-2">
          <div class="flex justify-between items-center text-[10px] font-bold uppercase tracking-wider">
            <div class="flex items-center gap-2 text-neutral-200">
               <Maximize :size="14" />
               <span>Scale Factor</span>
            </div>
            <span class="text-white font-mono px-2 py-0.5 rounded">{{ scaleFactor.toFixed(2) }}</span>
          </div>
          <input type="range" v-model.number="scaleFactor" min="0.05" max="1.0" step="0.01" @change="convert" class="w-full h-1 rounded-full appearance-none accent-white cursor-pointer" :style="getSliderStyle(scaleFactor, 0.05, 1.0)" />
        </div>

        <div class="flex flex-col gap-2">
          <div class="flex justify-between items-center text-[10px] font-bold uppercase tracking-wider">
            <div class="flex items-center gap-2 text-neutral-200">
               <Sun :size="14" />
               <span>Brightness</span>
            </div>
            <span class="text-white font-mono px-2 py-0.5 rounded">{{ brightness.toFixed(2) }}</span>
          </div>
          <input type="range" v-model.number="brightness" min="0.5" max="2.0" step="0.05" @change="convert" class="w-full h-1 rounded-full appearance-none accent-white cursor-pointer" :style="getSliderStyle(brightness, 0.5, 2.0)" />
        </div>

        <div class="flex flex-col gap-2">
          <div class="flex justify-between items-center text-[10px] font-bold uppercase tracking-wider">
            <div class="flex items-center gap-2 text-neutral-200">
               <Contrast :size="14" />
               <span>Contrast</span>
            </div>
            <span class="text-white font-mono px-2 py-0.5 rounded">{{ contrast.toFixed(2) }}</span>
          </div>
          <input type="range" v-model.number="contrast" min="0.5" max="2.0" step="0.05" @change="convert" class="w-full h-1 rounded-full appearance-none accent-white cursor-pointer" :style="getSliderStyle(contrast, 0.5, 2.0)" />
        </div>

        <div class="flex flex-col gap-2">
          <div class="flex justify-between items-center text-[10px] font-bold uppercase tracking-wider">
            <div class="flex items-center gap-2 text-neutral-200">
               <Droplet :size="14" />
               <span>Saturation</span>
            </div>
            <span class="text-white font-mono px-2 py-0.5 rounded">{{ saturation.toFixed(2) }}</span>
          </div>
          <input type="range" v-model.number="saturation" min="0.5" max="2.0" step="0.05" @change="convert" class="w-full h-1 rounded-full appearance-none accent-white cursor-pointer" :style="getSliderStyle(saturation, 0.5, 2.0)" />
        </div>
      </div>

      <button 
        class="mt-auto bg-neutral-900 text-neutral-200 border-none py-4 rounded-full font-black text-[10px] uppercase tracking-[0.2em] cursor-pointer disabled:cursor-not-allowed transition-all duration-300 hover:bg-neutral-800 flex items-center justify-center gap-2"
        :disabled="!filepath || isConverting" 
        @click="resultImagePath ? openResultImage() : convert()"
      >
        <template v-if="!isConverting">
          <template v-if="resultImagePath">
            <span>Open Result</span>
          </template>
          <template v-else>
            <span>{{ filepath ? 'Live Mode Ready' : 'Select Image First' }}</span>
          </template>
        </template>
        <RefreshCw v-else class="w-4 h-4 animate-spin" />
      </button>
    </aside>

    <!-- Main Content -->
    <main class="flex-1 flex flex-col glass-panel rounded-[20px] lg:rounded-[28px] overflow-hidden min-h-[500px] relative">
      <div class="flex-1 flex flex-col p-6 min-h-0">
        <div v-if="resultImagePath" class="absolute top-6 left-6 z-10 bg-neutral-900/80 backdrop-blur border border-neutral-800 rounded-2xl px-4 py-2 text-[10px] text-neutral-400 shadow-2xl">
          <code>{{ resultImagePath }}</code>
        </div>

        <div class="flex-1 flex justify-center items-center">
          <div v-if="displayImagePath" class="flex flex-col items-center gap-4 flex-1">
            <img :src="displayImagePath" alt="ASCII Art" class="max-w-full max-h-[60vh] lg:max-h-[70vh] object-contain rounded-lg shadow-2xl border border-white/10" />
          </div>
          <div v-else class="flex-1 flex justify-center items-center text-neutral-500 italic text-sm text-center p-10">
            {{ isConverting ? 'Processing Image...' : 'Select an image to start' }}
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
/* Scoped styles removed in favor of Tailwind CSS */
</style>
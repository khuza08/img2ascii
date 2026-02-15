<script setup lang="ts">
import { getCurrentWindow } from "@tauri-apps/api/window";
import { X, Minus, Square } from "lucide-vue-next";

const appWindow = getCurrentWindow();

function startDrag(e: PointerEvent) {
  // Only drag if left mouse button is pressed and not on a button
  if (e.button === 0 && !(e.target as HTMLElement).closest('button')) {
    appWindow.startDragging();
  }
}
</script>

<template>
  <div
    @pointerdown="startDrag"
    class="h-10 flex items-center px-4 shrink-0 select-none bg-black/40 backdrop-blur-md border-b border-white/5 z-50 rounded-t-[20px] lg:rounded-t-[28px] cursor-default"
  >
    <div class="flex items-center gap-2 group mr-4 z-60">
      <button
        @click="appWindow.close()"
        class="w-3 h-3 rounded-full bg-[#ff5f57] flex items-center justify-center relative overflow-hidden transition-all active:brightness-75 hover:opacity-80 group-hover:shadow-[inset_0_0_0_1px_rgba(0,0,0,0.1)]"
      >
        <X :size="8" class="text-black/60 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
      </button>
      <button
        @click="appWindow.minimize()"
        class="w-3 h-3 rounded-full bg-[#febc2e] flex items-center justify-center relative overflow-hidden transition-all active:brightness-75 hover:opacity-80 group-hover:shadow-[inset_0_0_0_1px_rgba(0,0,0,0.1)]"
      >
        <Minus :size="8" class="text-black/60 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
      </button>
      <button
        @click="appWindow.toggleMaximize()"
        class="w-3 h-3 rounded-full bg-[#28c840] flex items-center justify-center relative overflow-hidden transition-all active:brightness-75 hover:opacity-80 group-hover:shadow-[inset_0_0_0_1px_rgba(0,0,0,0.1)]"
      >
        <Square :size="7" class="text-black/60 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
      </button>
    </div>

    <div class="flex-1 flex justify-center pointer-events-none">
      <span class="text-[9px] font-black uppercase tracking-[0.4em] text-white/20">img2ascii</span>
    </div>
  </div>
</template>

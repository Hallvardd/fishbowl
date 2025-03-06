<template>
  <div>
    <FishBowl />
  </div>
</template>

<script>
import FishBowl from './components/FishBowl.vue'

export default {
  name: 'App',
  components: {
    FishBowl
  }
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}
</style>

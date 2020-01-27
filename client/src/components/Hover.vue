<template>
  <div
    @mouseover="hover = true"
    @mouseleave="hover = false"
  />
</template>
<script>
export default {
  data() {
    return {
      hover: false,
    };
  }
}
</script>
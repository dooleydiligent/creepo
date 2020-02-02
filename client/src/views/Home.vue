<template>
  <layout name="LayoutDefault">
    <div class="Home">
      <h1>Caching Repository</h1>
      <p>
        Cache build artifacts for maven, npm, pip, and others
      </p>
    </div>
  </layout>
</template>

<script>
import Layout from '../layouts/Layout';
export default {
  name: `Home`,
  components: {
    Layout,
  },
};
</script>
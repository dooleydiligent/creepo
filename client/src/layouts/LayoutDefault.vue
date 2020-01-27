<template>
  <div class="LayoutDefault">
    <pageheader class="LayoutDefault__nav"/>
    <main class="LayoutDefault__main">
      <slot />
    </main>
    <footer class="LayoutDefault__footer">
      &copy; Dooley Diligent, LLC
    </footer>
  </div>
</template>

<script>
import Header from '../components/Header.vue';
export default {
  name: `LayoutDefault`,
  components: {
    pageheader: Header,
  },
  data() {
    return {
      hover: false,
      user: null
    };
  },
};
</script>

<style lang="scss">
.LayoutDefault {
  max-width: 90%;
  margin-right: auto;
  margin-left: auto;
  padding-right: 1em;
  padding-left: 1em;
  &__nav {
    padding-top: 1em;
    padding-bottom: 1em;
    border-bottom: 1px solid #c0c0c0;
  }
  &__main {
    padding-top: 1.5em;
    padding-bottom: 2em;
  }
  &__footer {
    padding-top: 1em;
    padding-bottom: 1em;
    border-top: 1px solid #c0c0c0;
  }
  .active {
    background: #B2CED9;
  }
  .pageheader {
    max-width: 100%
  }
}
</style>

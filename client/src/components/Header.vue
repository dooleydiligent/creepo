<template>
  <nav style='width:90%'>
    <router-link to="/">Home</router-link> |
    <router-link to="/about">About</router-link>
    <div class="user">
      <span v-if="!user" @mouseover="hover = true" @mouseleave="hover = false" :class="{ active: hover }">Sign In</span>
    </div>
  </nav>
</template>

<script>
export default {
  data() {
    console.log(`This is data`);
    return {
      hover: false,
      user: null
    };
  },
  created() {
    // Simulate fetching user data.
    setTimeout(() => {
      this.user = null;
    }, 2000);
  }
};
</script>
<style>
.user {
    float: right;
  }
</style>

<template>
  <div id="quiz-maker">
    <div class="q-maker relative">
      <component :is="QuizMaker.Questions[$store.getters.question.type].view"
                 class="q-question"
                 :class="`q-${$store.getters.question.type}`"
                 :value="$store.getters.question"/>
    </div>
  </div>
</template>

<script>
import { QuizMaker } from '@/app/QuizMaker'

export default {
  name: 'QuizMakerView',
  data () {
    return {
      QuizMaker,
    }
  },
}
</script>
<style>
.q-maker {
  font-family: Arial;
}
</style>

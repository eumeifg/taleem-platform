import Vue from 'vue'
import Vuex from 'vuex'
import { QuizMaker } from '@/app/QuizMaker'
import { Checkboxes } from '../questions/checkboxes/Checkboxes'
import { merge, flatten } from 'lodash'
Vue.use(Vuex)
export default new Vuex.Store({
  state: {
    features: {
      checkboxes: {
        explanation: true,
        customScript: true,
        optionHints: true,
        compoundFeedback: true,
        partialCredit: true,
      },
      dropdown: {
        optionHints: true,
      },
      'multi-choice': {
        optionHints: true,
      },
      'numerical-input': {
        tolerance: true,
        trailingText: true,
        partialCredit: true,
      },
      'text-input': {
        feedback: true,
        trailingText: true,
      },
    },
    ui: {
      showFooter: true,
      submitText: 'Submit',
      cancelText: 'Cancel',
      showAddQuestionBtn: true,
      addQuestionText: 'Add new question',
    },
    lib: null as null | QuizMaker,
    question: Checkboxes.makeNew(),
    questions: [
      Checkboxes.makeNew(),
    ],
    rootEl: document.body as any,
  },
  getters: {
    features: state => state.features,
    ui: state => state.ui,
    question: state => state.question,
    questions: state => state.questions,
    lib: state => state.lib,
    validationErrors: state => {
      return QuizMaker.Questions[state.question.type].validate(state.question as any)
    },
    hasAnyValidationErrors: (state, getters) => {
      return !!flatten(Object.values(getters.validationErrors)).length
    },
  },
  mutations: {
    SET_FEATURES_CONFIG (state, config) {
      state.features = merge(state.features, config)
    },
    SET_UI (state, ui) {
      state.ui = ui
    },
    SET_QUESTION (state, question) {
      state.question = question
    },
    SET_LIB_INSTANCE (state, instance) {
      state.lib = instance
    },
  },
  actions: {},
  modules: {},
})

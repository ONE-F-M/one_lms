<template>
  <div class="border-2 rounded-md min-w-80 max-w-sm p-5">
    <div v-if="course.data">
      <router-link
        class="btn btn-primary wide-button"
        id="continue-learning"
        :to="continueLearningUrl"
      >
        {{ continueLearningText }}
      </router-link>

      <router-link
        v-if="showCertificateButton"
        class="btn btn-secondary wide-button mt-2"
        :to="certificateUrl"
      >
        View Certificate
      </router-link>

      <p v-if="maxAttemptsExceeded" class="text-danger mt-2">
        You have exceeded the maximum number of attempts allowed to appear for evaluations of this course.
      </p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { Button } from 'frappe-ui';

const props = defineProps({
  course: {
    type: Object,
    required: true,
  },
});

const membership = computed(() => props.course.data.membership);
const progress = computed(() => (membership.value ? Math.round(membership.value.progress) : 0));

const continueLearningText = computed(() => {
  if (membership.value) {
    if (progress.value === 0) {
      return 'Start Learning';
    } else if (progress.value === 100) {
      return 'Course Completed';
    } else {
      return `${progress.value}% Completed, Continue Learning`;
    }
  }
  return 'Continue Learning';
});

const continueLearningUrl = computed(() => {
    if (props.course.data.current_lesson) {
        const [chapter, lesson] = props.course.data.current_lesson.split('-');
        return {
            name: 'Lesson',
            params: {
                courseName: props.course.data.name,
                chapterNumber: chapter,
                lessonNumber: lesson
            }
        }
    }
    // Fallback to the first lesson if current_lesson is not available
    return {
        name: 'Lesson',
        params: {
            courseName: props.course.data.name,
            chapterNumber: 1,
            lessonNumber: 1
        }
    }
});

const showCertificateButton = computed(() => {
  return membership.value && props.course.data.enable_certification && membership.value.certificate;
});

const certificateUrl = computed(() => {
    if (!showCertificateButton.value) return '';
    return {
        name: 'CourseCertification',
        params: {
            courseName: props.course.data.name
        }
    }
});

const maxAttemptsExceeded = computed(() => {
  return membership.value && membership.value.max_attempts_exceeded;
});
</script>

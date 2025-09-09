<template>
  <div>
    <router-link
      v-if="course"
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
</template>

<script setup>
import { computed } from 'vue';
import { __ } from 'frappe-ui';

const props = defineProps({
  course: {
    type: Object,
    required: true,
  },
});

const membership = computed(() => props.course.membership);
const progress = computed(() => (membership.value ? Math.round(membership.value.progress) : 0));

const continueLearningText = computed(() => {
  if (membership.value) {
    if (progress.value === 0) {
      return __('Start Learning');
    } else if (progress.value === 100) {
      return __('Course Completed');
    } else {
      return __('{0}% Completed, Continue Learning', [progress.value]);
    }
  }
  return __('Continue Learning');
});

const continueLearningUrl = computed(() => {
    if (!props.course.next_lesson) {
        return { name: 'CourseDetail', params: { courseName: props.course.name } };
    }
    const { chapter, lesson } = props.course.next_lesson;
    return {
        name: 'Lesson',
        params: {
            courseName: props.course.name,
            chapterNumber: chapter,
            lessonNumber: lesson
        }
    }
});

const showCertificateButton = computed(() => {
  return membership.value && props.course.enable_certification && membership.value.certificate;
});

const certificateUrl = computed(() => {
    if (!showCertificateButton.value) return '';
    return {
        name: 'CourseCertification',
        params: {
            courseName: props.course.name
        }
    }
});

const maxAttemptsExceeded = computed(() => {
  return membership.value && membership.value.max_attempts_exceeded;
});

</script>

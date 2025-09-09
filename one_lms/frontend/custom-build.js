const fs = require('fs-extra');
const path = require('path');

// Assuming this script is in one_lms/frontend/
const oneLmsAppDir = path.resolve(__dirname, '..');

// Path to the lms app, assuming it's a sibling of one_lms
const lmsAppDir = path.resolve(oneLmsAppDir, '..', 'lms');

const overrides = [
    {
        // The overridden CourseDetail.vue from our app
        source: path.resolve(__dirname, 'src', 'pages', 'CourseDetail.vue'),
        // The target path in the original lms app
        target: path.resolve(lmsAppDir, 'frontend', 'src', 'pages', 'CourseDetail.vue')
    },
    {
        // The new component we created
        source: path.resolve(__dirname, 'src', 'components', 'CustomCourseButtons.vue'),
        // The target path in the original lms app
        target: path.resolve(lmsAppDir, 'frontend', 'src', 'components', 'CustomCourseButtons.vue')
    }
];

function overrideFiles() {
    console.log('Starting to override files...');
    overrides.forEach(override => {
        if (fs.existsSync(override.source)) {
            console.log(`Copying ${override.source} to ${override.target}`);
            fs.copySync(override.source, override.target, { overwrite: true });
        } else {
            console.error(`Source file not found: ${override.source}`);
        }
    });
    console.log('File override process completed.');
}

// Check if the lms app directory exists
if (fs.existsSync(lmsAppDir)) {
    overrideFiles();
} else {
    console.error(`LMS app directory not found at ${lmsAppDir}`);
    console.error('Please make sure the LMS app is installed and the paths are correct.');
}

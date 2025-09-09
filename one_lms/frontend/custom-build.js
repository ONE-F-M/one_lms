const fs = require('fs-extra');
const path = require('path');

// Assuming this script is in one_lms/frontend/
const oneLmsAppDir = path.resolve(__dirname, '..');

// Path to the lms app, assuming it's a sibling of one_lms
const lmsAppDir = path.resolve(oneLmsAppDir, '..', 'lms');

const sourceOverrides = [
    {
        source: path.resolve(__dirname, 'src', 'components', 'CourseCardOverlay.vue'),
        target: path.resolve(lmsAppDir, 'frontend', 'src', 'components', 'CourseCardOverlay.vue')
    }
];


function overrideSourceFiles() {
    console.log('Starting to override source files...');
    sourceOverrides.forEach(override => {
        if (fs.existsSync(override.source)) {
            console.log(`Copying ${override.source} to ${override.target}`);
            fs.copySync(override.source, override.target, { overwrite: true });
        } else {
            console.error(`Source file not found: ${override.source}`);
        }
    });
    console.log('Source file override process completed.');
}

if (fs.existsSync(lmsAppDir)) {
    overrideSourceFiles();
} else {
    console.error(`LMS app directory not found at ${lmsAppDir}`);
    console.error('Please make sure the LMS app is installed and the paths are correct.');
}

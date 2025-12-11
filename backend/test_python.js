/**
 * Test script to verify Python path detection
 * Run: node backend/test_python.js
 */

const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');

/**
 * Get Python path from venv or system
 */
function getPythonPath() {
    // Check if PYTHON_PATH is explicitly set in .env
    if (process.env.PYTHON_PATH) {
        return process.env.PYTHON_PATH;
    }

    // Try to find Python in venv
    const venvPath = path.join(__dirname, 'venv');
    const isWindows = process.platform === 'win32';

    const venvPythonPath = isWindows
        ? path.join(venvPath, 'Scripts', 'python.exe')
        : path.join(venvPath, 'bin', 'python');

    // Check if venv Python exists
    try {
        if (fs.existsSync(venvPythonPath)) {
            console.log(`✅ Using venv Python: ${venvPythonPath}`);
            return venvPythonPath;
        }
    } catch (err) {
        // If file check fails, continue to system Python
    }

    // Fallback to system Python
    console.log('⚠️ Using system Python (venv not found)');
    return isWindows ? 'python' : 'python3';
}

// Test the detection
console.log('=== Python Path Detection Test ===\n');

const pythonPath = getPythonPath();
console.log(`Detected Python path: ${pythonPath}\n`);

// Test if Python works
console.log('Testing Python execution...\n');

const pythonProcess = spawn(pythonPath, ['--version']);

pythonProcess.stdout.on('data', (data) => {
    console.log(`✅ Python version: ${data.toString().trim()}`);
});

pythonProcess.stderr.on('data', (data) => {
    console.log(`${data.toString().trim()}`);
});

pythonProcess.on('close', (code) => {
    if (code === 0) {
        console.log('\n✅ Python is working correctly!');

        // Test if required packages are installed
        console.log('\nChecking installed packages...\n');
        const pipList = spawn(pythonPath, ['-m', 'pip', 'list']);

        let packages = '';
        pipList.stdout.on('data', (data) => {
            packages += data.toString();
        });

        pipList.on('close', () => {
            const requiredPackages = ['playwright', 'beautifulsoup4', 'lxml', 'requests'];
            console.log('Required packages status:');
            requiredPackages.forEach(pkg => {
                const installed = packages.toLowerCase().includes(pkg.toLowerCase());
                console.log(`  ${installed ? '✅' : '❌'} ${pkg}`);
            });

            console.log('\n=== Test Complete ===');
        });
    } else {
        console.log(`\n❌ Python execution failed with code ${code}`);
        console.log('\nTroubleshooting:');
        console.log('1. Ensure Python 3.8+ is installed');
        console.log('2. Run: npm run setup');
        console.log('3. Check that backend/venv folder exists');
    }
});

pythonProcess.on('error', (error) => {
    console.log(`\n❌ Error: ${error.message}`);
    console.log('\nTroubleshooting:');
    console.log('1. Ensure Python 3.8+ is installed');
    console.log('2. Run: npm run setup');
    console.log('3. Check that backend/venv folder exists');
});

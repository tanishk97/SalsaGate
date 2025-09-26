const core = require('@actions/core');
const fs = require('fs');
const path = require('path');

async function run() {
  try {

    const outputPath = path.join(process.cwd(), 'goodbye_world.json');

    const content = {
      message: `Goodbye World!`,
      timestamp: new Date().toISOString(),
    };

    fs.writeFileSync(outputPath, JSON.stringify(content, null, 2));

    console.log(`✅ File generated: ${outputPath}`);
    core.setOutput('filepath', outputPath);
  } catch (error) {
    core.setFailed(error.message);
  }
}

run();
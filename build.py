import os
import subprocess
from datetime import datetime
from dotenv import load_dotenv
from pydantic import BaseModel, Field

class AppVersion(BaseModel):
    version: str = Field(..., pattern=r'^\d{2}\.\d{2}\.\d{2}\.\d{2}\.\d{2}$')

class DockerBuilder:
    def __init__(self):
        load_dotenv('cfg/.build')
        self.image_name = os.getenv('IMAGE_NAME', 'b3')
        self.platform = os.getenv('PLATFORM', 'linux/amd64')
        self.version_file = os.getenv('VERSION_FILE', 'cfg/version.txt')

    def get_current_version(self) -> AppVersion:
        if os.path.exists(self.version_file):
            with open(self.version_file, 'r') as f:
                return AppVersion(version=f.read().strip())
        return self.generate_new_version()

    def generate_new_version(self) -> AppVersion:
        now = datetime.now()
        return AppVersion(version=now.strftime("%y.%m.%d.%H.%M"))

    def update_version(self, version: AppVersion):
        with open(self.version_file, 'w') as f:
            f.write(version.version)

    def update_dockerfile(self, version: AppVersion):
        with open('Dockerfile', 'r') as f:
            lines = f.readlines()

        updated_lines = []
        for line in lines:
            if line.startswith('FROM'):
                updated_lines.append(line)
                updated_lines.append(f'LABEL version="{version.version}"\n')
            else:
                updated_lines.append(line)

        with open('Dockerfile', 'w') as f:
            f.writelines(updated_lines)

    def build_image(self, version: AppVersion):
        cmd = f"docker buildx build --platform {self.platform} -t {self.image_name}:{version.version} --load ."
        subprocess.run(cmd, shell=True, check=True)

    def pack_image(self, version: AppVersion):
        cmd = f"docker save -o {self.image_name}.tar {self.image_name}:{version.version}"
        subprocess.run(cmd, shell=True, check=True)

    def run(self):
        current_version = self.get_current_version()
        new_version = self.generate_new_version()
        self.update_version(new_version)
        self.update_dockerfile(new_version)
        self.build_image(new_version)
        self.pack_image(new_version)
        print(f"Successfully built and packed version {new_version.version}")

if __name__ == "__main__":
    builder = DockerBuilder()
    builder.run()
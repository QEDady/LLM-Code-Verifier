# LLM-Code-Verifier

## Development Environment Setup with Dev Containers

This project uses Dev Containers to provide a consistent and reproducible development environment. Follow the steps below to set up and use the development environment.

### Prerequisites

1. **Linux**: This development environment is designed to run on a Linux operating system.
2. **Docker**: Ensure Docker is installed on your machine. You can download it from [Docker's official website](https://www.docker.com/get-started).
3. **Visual Studio Code**: Install Visual Studio Code from [here](https://code.visualstudio.com/).
4. **Dev Containers Extension**: Install the Dev Containers extension for Visual Studio Code. You can find it in the [Visual Studio Code Marketplace](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers).

### Setting Up the Development Environment

1. **Clone the Repository**:
    ```sh
    git clone https://github.com/QEDady/LLM-Code-Verifier.git
    cd LLM-Code-Verifier
    ```

2. **Open the Project in Visual Studio Code**:
    ```sh
    code .
    ```

3. **Reopen in Container**:
    - Once the project is open in Visual Studio Code, you should see a prompt asking if you want to reopen the project in a container. Click "Reopen in Container".
    - If you don't see the prompt, you can manually reopen the project in a container by pressing `F1` and selecting `Dev Containers: Reopen in Container` or `Dev Containers: Rebuild and Reopen in Container`.

### Using the Development Environment

- **Terminal Access**: You can access the terminal within the container by opening a new terminal in Visual Studio Code (``` Ctrl+` ```).
- **Running Commands**: Any commands you run in the terminal will be executed inside the container, ensuring a consistent environment.
- **Installing Dependencies**: If you need to install additional dependencies, you can do so within the container. These changes will be isolated from your host machine.

### Customizing the Dev Container

The environment is designed using Dev Container, Dockerfile, Docker Compose file, prestart, and postcreate scripts.

- **Adding Core Dependencies/Packages**: Add core dependencies and packages in the `Dockerfile`.
- **Adding Python Libraries**: Add Python libraries to the `requirements.txt` file. You can do this by running the following command after installing the package:
    ```sh
    pip freeze > requirements.txt
    ```
- **Adding a VS Code Extension Permanently**: To add a VS Code extension permanently, right-click on the extension in the Extensions view and select "Add to devcontainer.json".

For more information on Dev Containers, refer to the [official documentation](https://code.visualstudio.com/docs/remote/containers).

---

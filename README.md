# **CACAO Knowledge Base**  

![License](https://img.shields.io/badge/license-MIT-blue.svg)  

## **Overview**  
This repository contains an implementation of a **CACAO Playbook Knowledge Base**, which enables easy storage, retrieval, and management of CACAO playbooks throughout their lifecycle.  

⚠ **Note:** This project is provided **as-is**, with **no support or future updates**.

⚠ **Warning:** This project was developed for **research purposes only** and is **not intended for production use**.

## **Features**  
- **Backend:** The backend is built using **FastAPI**, a modern web framework for building APIs with Python. It provides high performance and automatic OpenAPI documentation, making it efficient for managing CACAO playbooks
- **Frontend:** The frontend is developed using **Retool**, a low-code platform that enables rapid UI development. It provides a user-friendly interface for interacting with the system
- **Submodules:**
  - **SOARCA** – Execution reporting for playbooks  
  - **CACAO Roaster** – Playbook processing tools  
  - **CTI TAXII Server** – Sharing playbooks using a TAXII-based server  

## **Installation & Usage**  
To get started, clone the repository with submodules:  

```sh
git clone --recurse-submodules https://github.com/Orestistsira/cacao-knowledge-base.git
cd cacao-knowledge-base
```

Follow the setup instructions for the backend, the frontend and the submodules in their respective folders.

## **Contributing**  
Contributions are welcome, but please note that this repository is **not actively maintained**. If you find any issues or have improvements, feel free to fork the project and modify it as needed.

## **License**  
This project is licensed under the **MIT License** – see the [LICENSE](LICENSE) file for details.

## **Acknowledgments**  
This project builds upon existing open-source efforts, including:  

- **[SOARCA](https://github.com/COSSAS/SOARCA)**  
- **[CACAO Roaster](https://github.com/opencybersecurityalliance/cacao-roaster)**  
- **[CTI TAXII Server](https://github.com/oasis-open/cti-taxii-server)**  


# **CACAO Knowledge Base**  

![License](https://img.shields.io/badge/license-MIT-blue.svg)  

## **Overview**  
This repository contains an implementation of a **CACAO Playbook Knowledge Base**, which enables easy storage, retrieval, and management of CACAO v2.0 playbooks throughout their lifecycle.

The CACAO Standard is an open standard designed to structure and automate cybersecurity playbooks. It provides a standardized format for defining, sharing, and executing security procedures, helping organizations improve incident response. For wider adoption of the CACAO specification, we provide a dedicated Knowledge Base to simplify the management, execution, and sharing of CACAO playbooks.

The CACAO Knowledge Base platform complies fully to the [**CACAO v2.0 specification**](https://docs.oasis-open.org/cacao/security-playbooks/v2.0/security-playbooks-v2.0.pdf).

⚠ **Note:** This project was developed for **research purposes only** and is **not intended for production use**.

## **Project Status**

This project is provided **as-is**, with **no support or future updates**.

## **Features**  
- **Backend:** The backend is built using **FastAPI**, a modern web framework for building APIs with Python. It provides high performance and automatic OpenAPI documentation, making it efficient for managing CACAO playbooks
- **Frontend:** The frontend is developed using **Retool**, a low-code platform that enables rapid UI development. It provides a user-friendly interface for interacting with the system
- **Submodules:**
  - **SOARCA** – A SOAR tool, used for the execution of CACAO playbooks and execution status reporting 
  - **CACAO Roaster** – A web application for generating, parsing and validating, manipulating, and visualizing CACAO playbooks
  - **CTI TAXII Server** – A minimal implementation of a TAXII 2.1 Server, used for sharing CACAO playbooks

## **Demo**  
Watch a demonstration of the **CACAO Playbook Knowledge Base** in action:  

▶ [**Watch on YouTube**](https://youtu.be/6fGhg02aMlg)

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


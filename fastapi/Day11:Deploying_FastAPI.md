This video marks the final installment of the API playlist by *CampusX*, focusing on the **deployment of a FastAPI application** onto *AWS* (Amazon Web Services). 

### **Project Overview**
Throughout this playlist, a machine learning model for **insurance premium prediction** was built, served via a *FastAPI* endpoint, containerized using *Docker*, and pushed to *Docker Hub*. This final step covers hosting that containerized image on an *AWS EC2* instance.

### **Deployment Steps**
1. **AWS Setup (5:06 - 9:55):** Create an *AWS* account and launch an *EC2* instance. Use an *Ubuntu* OS with the *T2 Micro* instance type (free tier eligible). Ensure the *SSH* traffic rule is set to 'Anywhere'.
2. **Connecting & Configuration (9:57 - 12:45):** Connect to the instance via the *AWS Console*. Run the following commands to set up the environment:
   * `sudo apt-get update`
   * `sudo apt-get install -y docker.io`
   * `sudo systemctl start docker`
   * `sudo systemctl enable docker`
   * `sudo usermod -aG docker $USER`
   * After running these, exit and restart the connection.
3. **Running the API (13:10 - 14:05):** Pull the *Docker* image from *Docker Hub* using `docker pull <image_path>` and execute it with `docker run -p 8000:8000 <image_path>`.
4. **Security Group Settings (14:49 - 15:37):** Access the *Security* tab in the *EC2* dashboard, edit inbound rules, and add a custom *TCP* rule for **port 8000** to allow external traffic.
5. **Verification & Frontend (15:38 - 17:35):** Test the API via the public *IP* address (e.g., `http://<public-ip>:8000`). Update the frontend code (Streamlit application) to point to the new *AWS* public *IP* instead of `localhost`.

### **Key Takeaways**
* The process demonstrates a standard workflow for a machine learning engineer to transition from local development to cloud production.
* *CampusX* announces a upcoming **paid, advanced FastAPI course** that will dive deeper into production-level concepts.
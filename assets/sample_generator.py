"""Utility script to generate realistic PDF resumes for testing AI Recruiter."""
import os
from pathlib import Path
import fitz  # PyMuPDF

SAMPLE_RESUMES = [
    {
        "file_name": "Alex_Rivera_Senior_Python_Backend.pdf",
        "name": "Alex Rivera",
        "title": "Senior Python Backend Engineer",
        "email": "alex.rivera@example.com",
        "phone": "+1 (555) 234-5678",
        "location": "San Francisco, CA",
        "linkedin": "https://linkedin.com/in/alexrivera-tech",
        "github": "https://github.com/alexrivera-dev",
        "summary": "Senior Backend Software Engineer with 6+ years of experience designing and scaling distributed microservices, RESTful and gRPC APIs, and high-performance relational databases. Passionate about clean code, test-driven development, and cloud reliability.",
        "skills": "Python, FastAPI, Django, PostgreSQL, Redis, Docker, Kubernetes, AWS, REST API, Git, CI/CD, Microservices, Celery, Unit Testing, Linux",
        "experience": [
            {
                "role": "Senior Backend Engineer",
                "company": "Apex Cloud Systems",
                "dates": "2021 - Present",
                "bullets": [
                    "Architected high-throughput microservices using Python FastAPI and PostgreSQL handling 50M+ requests daily.",
                    "Implemented Redis caching layer, reducing average API response latencies by 42%.",
                    "Containerized 15+ backend services using Docker and orchestrated deployments on Kubernetes (EKS).",
                    "Led team CI/CD pipeline modernization using GitHub Actions and AWS ECS."
                ]
            },
            {
                "role": "Software Engineer",
                "company": "DataStream Analytics",
                "dates": "2018 - 2021",
                "bullets": [
                    "Developed backend data ingestion pipelines in Python and Django with PostgreSQL.",
                    "Designed RESTful APIs used by web and mobile client applications.",
                    "Wrote automated unit and integration test suites with PyTest, maintaining 90%+ code coverage."
                ]
            }
        ],
        "education": "Bachelor of Science in Computer Science, University of California, Berkeley (2014 - 2018)",
        "certifications": "AWS Certified Solutions Architect – Associate (2022)"
    },
    {
        "file_name": "Sophia_Chen_Full_Stack_Developer.pdf",
        "name": "Sophia Chen",
        "title": "Full Stack Software Developer",
        "email": "sophia.chen@example.com",
        "phone": "+1 (555) 345-6789",
        "location": "Seattle, WA",
        "linkedin": "https://linkedin.com/in/sophiachen-dev",
        "github": "https://github.com/sophiachen",
        "summary": "Dynamic Full Stack Developer with 4 years of hands-on experience building modern, responsive web applications using React, TypeScript, Node.js, Express, and MongoDB. Strong focus on user experience and scalable REST APIs.",
        "skills": "JavaScript, TypeScript, React, Next.js, Node.js, Express.js, MongoDB, GraphQL, HTML5, CSS3, Tailwind CSS, Redux, Docker, Git, REST API, AWS",
        "experience": [
            {
                "role": "Full Stack Developer",
                "company": "Vanguard Web Studios",
                "dates": "2021 - Present",
                "bullets": [
                    "Developed responsive web applications with React, Next.js, and TypeScript serving 100K+ monthly active users.",
                    "Built scalable REST and GraphQL APIs with Node.js and Express connected to MongoDB.",
                    "Styled accessible UI components with Tailwind CSS and managed complex global state with Redux.",
                    "Integrated Stripe payment gateways and third-party SaaS authentication."
                ]
            },
            {
                "role": "Junior Web Developer",
                "company": "Northwest Digital",
                "dates": "2020 - 2021",
                "bullets": [
                    "Created interactive frontend interfaces with React, JavaScript, HTML5, and CSS3.",
                    "Collaborated with UX designers to translate Figma mockups into pixel-perfect web pages.",
                    "Utilized Git for collaborative version control and agile sprint planning."
                ]
            }
        ],
        "education": "Bachelor of Science in Software Engineering, University of Washington (2016 - 2020)",
        "certifications": "Meta Certified Front-End Developer (2021)"
    },
    {
        "file_name": "Marcus_Johnson_DevOps_Cloud_Architect.pdf",
        "name": "Marcus Johnson",
        "title": "DevOps & Cloud Infrastructure Architect",
        "email": "marcus.johnson@example.com",
        "phone": "+1 (555) 456-7890",
        "location": "Austin, TX",
        "linkedin": "https://linkedin.com/in/marcusjohnson-cloud",
        "github": "https://github.com/marcus-ops",
        "summary": "Results-oriented Cloud & DevOps Architect with 7+ years of expertise designing resilient multi-cloud architectures on AWS, automating deployments with Terraform and Kubernetes, and building zero-downtime CI/CD pipelines.",
        "skills": "AWS, Docker, Kubernetes, Terraform, Linux, CI/CD, Jenkins, GitHub Actions, Bash, Ansible, Prometheus, Grafana, Python, Helm, Nginx, Security",
        "experience": [
            {
                "role": "Lead DevOps Engineer",
                "company": "OmniCloud Solutions",
                "dates": "2020 - Present",
                "bullets": [
                    "Engineered cloud infrastructure on AWS using Terraform and CloudFormation across 3 global regions.",
                    "Orchestrated multi-tenant Kubernetes (EKS) clusters supporting 200+ containerized microservices.",
                    "Automated end-to-end continuous integration and deployment with GitHub Actions and Jenkins.",
                    "Implemented real-time monitoring and alerting stacks with Prometheus, Grafana, and Datadog."
                ]
            },
            {
                "role": "Systems & DevOps Engineer",
                "company": "Hyperion Networks",
                "dates": "2017 - 2020",
                "bullets": [
                    "Administered enterprise Linux server clusters and configured Nginx reverse proxies.",
                    "Developed automation scripts in Bash and Python for infrastructure provisioning.",
                    "Enforced cloud security compliance and automated vulnerability scanning."
                ]
            }
        ],
        "education": "Bachelor of Science in Information Technology, Georgia Institute of Technology (2013 - 2017)",
        "certifications": "Certified Kubernetes Administrator (CKA), AWS Certified Solutions Architect Professional"
    },
    {
        "file_name": "Elena_Rostova_Data_Scientist.pdf",
        "name": "Elena Rostova",
        "title": "Data Scientist & Machine Learning Specialist",
        "email": "elena.rostova@example.com",
        "phone": "+1 (555) 567-8901",
        "location": "New York, NY",
        "linkedin": "https://linkedin.com/in/elenarostova-data",
        "github": "https://github.com/elena-ai",
        "summary": "Data Scientist with 5 years of experience building predictive machine learning models, NLP pipelines, and data analytics solutions. Proficient in Python, PyTorch, Scikit-Learn, SQL, and big data processing with Apache Spark.",
        "skills": "Python, Machine Learning, Scikit-Learn, PyTorch, Pandas, NumPy, SQL, Data Analysis, Deep Learning, NLP, Large Language Models, Apache Spark, Docker, AWS, Tableau, Statistics",
        "experience": [
            {
                "role": "Senior Data Scientist",
                "company": "NeuralInsight Labs",
                "dates": "2021 - Present",
                "bullets": [
                    "Trained and evaluated state-of-the-art NLP and transformer models using PyTorch and Hugging Face.",
                    "Constructed scalable feature engineering pipelines with Python, Pandas, and SQL processing 2TB+ daily data.",
                    "Built customer churn prediction models with Scikit-Learn improving retention by 18%.",
                    "Deployed containerized inference microservices using Docker on AWS EC2."
                ]
            },
            {
                "role": "Data Analyst / ML Researcher",
                "company": "FinData Corp",
                "dates": "2019 - 2021",
                "bullets": [
                    "Executed statistical regression and time-series forecasting on market telemetry.",
                    "Created interactive analytical dashboards in Tableau and Streamlit for executive stakeholders.",
                    "Automated ETL data workflows using SQL and Apache Spark."
                ]
            }
        ],
        "education": "Master of Science in Data Science, Stanford University (2017 - 2019)\nBachelor of Science in Mathematics, Boston University (2013 - 2017)",
        "certifications": "TensorFlow Developer Certificate (2020)"
    },
    {
        "file_name": "David_Kim_Junior_Frontend_Developer.pdf",
        "name": "David Kim",
        "title": "Junior Frontend Web Developer",
        "email": "david.kim@example.com",
        "phone": "+1 (555) 678-9012",
        "location": "San Jose, CA",
        "linkedin": "https://linkedin.com/in/davidkim-web",
        "github": "https://github.com/davidkim-ui",
        "summary": "Enthusiastic Junior Frontend Developer with 1.5 years of experience building responsive, user-friendly client-side web interfaces with React, JavaScript, HTML5, and CSS3. Eager to expand backend and cloud skills.",
        "skills": "JavaScript, React, HTML5, CSS3, Bootstrap, Git, jQuery, REST API, Webpack, Responsive Design",
        "experience": [
            {
                "role": "Junior Frontend Developer",
                "company": "PixelCraft Media",
                "dates": "2023 - Present",
                "bullets": [
                    "Built reusable React components for e-commerce client websites.",
                    "Implemented responsive CSS and Bootstrap styling ensuring mobile-first compatibility.",
                    "Integrated REST APIs to fetch and display dynamic product catalogs.",
                    "Participated in daily agile standups and code reviews."
                ]
            }
        ],
        "education": "Bachelor of Arts in Interactive Media Design, San Jose State University (2019 - 2023)",
        "certifications": "Certified JavaScript Developer (2023)"
    },
    {
        "file_name": "Rachel_Green_Technical_Product_Manager.pdf",
        "name": "Rachel Green",
        "title": "Technical Product Manager",
        "email": "rachel.green@example.com",
        "phone": "+1 (555) 789-0123",
        "location": "Boston, MA",
        "linkedin": "https://linkedin.com/in/rachelgreen-pm",
        "github": "https://github.com/rachelgreen-pm",
        "summary": "Strategic Technical Product Manager with 5+ years driving end-to-end product lifecycles, Agile sprint planning, user discovery, and cross-functional engineering execution for enterprise SaaS solutions.",
        "skills": "Product Management, Agile, Scrum, Jira, Confluence, User Research, System Design, Data Analysis, Roadmapping, Figma, Stakeholder Management",
        "experience": [
            {
                "role": "Technical Product Manager",
                "company": "Elevate SaaS Technologies",
                "dates": "2021 - Present",
                "bullets": [
                    "Led cross-functional team of 12 software engineers and UX designers to deliver enterprise SaaS platform.",
                    "Defined product vision, PRDs, user stories, and acceptance criteria in Jira and Confluence.",
                    "Analyzed product usage analytics and conducted user interviews to prioritize product roadmap."
                ]
            },
            {
                "role": "Associate Product Manager",
                "company": "Beacon Analytics",
                "dates": "2019 - 2021",
                "bullets": [
                    "Coordinated agile sprint planning, backlog grooming, and retrospective meetings.",
                    "Collaborated with customer success teams to resolve high-priority customer feature requests."
                ]
            }
        ],
        "education": "Master of Business Administration (MBA), Columbia University (2017 - 2019)\nBachelor of Arts in Economics, Boston College (2013 - 2017)",
        "certifications": "Certified Scrum Product Owner (CSPO)"
    }
]


def generate_pdf_resume(resume_data: dict, output_path: str):
    """Generates a clean, readable PDF resume using PyMuPDF."""
    doc = fitz.open()
    # Standard Letter page size: 612 x 792 points
    page = doc.new_page(width=612, height=792)

    # Margins and layout pointers
    x_left = 50
    y = 55
    line_height = 14

    # Header - Name & Title
    page.insert_text((x_left, y), resume_data["name"], fontsize=18, fontname="helv", color=(0.1, 0.15, 0.25))
    y += 18
    page.insert_text((x_left, y), resume_data["title"], fontsize=12, fontname="helv", color=(0.25, 0.4, 0.7))
    y += 16

    # Contact Line
    contact_line = f"{resume_data['email']}  |  {resume_data['phone']}  |  {resume_data['location']}"
    page.insert_text((x_left, y), contact_line, fontsize=9, fontname="helv", color=(0.4, 0.4, 0.4))
    y += 13
    links_line = f"LinkedIn: {resume_data['linkedin']}   GitHub: {resume_data['github']}"
    page.insert_text((x_left, y), links_line, fontsize=9, fontname="helv", color=(0.3, 0.45, 0.75))
    y += 18

    # Horizontal divider line
    page.draw_line(fitz.Point(x_left, y), fitz.Point(562, y), color=(0.8, 0.85, 0.9), width=1.5)
    y += 16

    # Professional Summary Section
    page.insert_text((x_left, y), "PROFESSIONAL SUMMARY", fontsize=11, fontname="helv", color=(0.1, 0.15, 0.25))
    y += 14
    summary_words = resume_data["summary"].split()
    summary_lines = []
    curr = []
    for w in summary_words:
        curr.append(w)
        if len(" ".join(curr)) > 90:
            summary_lines.append(" ".join(curr))
            curr = []
    if curr:
        summary_lines.append(" ".join(curr))
    
    for sl in summary_lines:
        page.insert_text((x_left, y), sl, fontsize=9.5, fontname="helv", color=(0.2, 0.2, 0.2))
        y += line_height
    y += 8

    # Technical Skills Section
    page.insert_text((x_left, y), "TECHNICAL SKILLS", fontsize=11, fontname="helv", color=(0.1, 0.15, 0.25))
    y += 14
    skills_text = f"Skills: {resume_data['skills']}"
    skill_words = skills_text.split()
    skill_lines = []
    curr = []
    for w in skill_words:
        curr.append(w)
        if len(" ".join(curr)) > 90:
            skill_lines.append(" ".join(curr))
            curr = []
    if curr:
        skill_lines.append(" ".join(curr))
    for skl in skill_lines:
        page.insert_text((x_left, y), skl, fontsize=9.5, fontname="helv", color=(0.2, 0.2, 0.2))
        y += line_height
    y += 8

    # Work Experience Section
    page.insert_text((x_left, y), "WORK EXPERIENCE", fontsize=11, fontname="helv", color=(0.1, 0.15, 0.25))
    y += 15

    for exp in resume_data["experience"]:
        # Title and Dates
        page.insert_text((x_left, y), f"{exp['role']} — {exp['company']}", fontsize=10, fontname="helv", color=(0.1, 0.15, 0.25))
        page.insert_text((420, y), exp["dates"], fontsize=9.5, fontname="helv", color=(0.4, 0.4, 0.4))
        y += 13

        for bullet in exp["bullets"]:
            bullet_words = bullet.split()
            b_lines = []
            curr = []
            for w in bullet_words:
                curr.append(w)
                if len(" ".join(curr)) > 85:
                    b_lines.append(" ".join(curr))
                    curr = []
            if curr:
                b_lines.append(" ".join(curr))

            for idx, bl in enumerate(b_lines):
                prefix = "• " if idx == 0 else "   "
                page.insert_text((x_left + 10, y), prefix + bl, fontsize=9, fontname="helv", color=(0.25, 0.25, 0.25))
                y += 12
        y += 6

    # Education Section
    page.insert_text((x_left, y), "EDUCATION", fontsize=11, fontname="helv", color=(0.1, 0.15, 0.25))
    y += 14
    for edu_line in resume_data["education"].split("\n"):
        page.insert_text((x_left, y), edu_line, fontsize=9.5, fontname="helv", color=(0.2, 0.2, 0.2))
        y += 13
    y += 6

    # Certifications Section
    if resume_data.get("certifications"):
        page.insert_text((x_left, y), "CERTIFICATIONS", fontsize=11, fontname="helv", color=(0.1, 0.15, 0.25))
        y += 14
        page.insert_text((x_left, y), resume_data["certifications"], fontsize=9.5, fontname="helv", color=(0.2, 0.2, 0.2))

    # Save to file
    doc.save(output_path)
    doc.close()


def generate_all_samples(output_dir: str = "data/sample_resumes"):
    """Generates all 6 sample PDF resumes in target directory."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    generated_paths = []
    for r in SAMPLE_RESUMES:
        out_file = os.path.join(output_dir, r["file_name"])
        generate_pdf_resume(r, out_file)
        generated_paths.append(out_file)
        print(f"Generated sample resume: {out_file}")
    return generated_paths


if __name__ == "__main__":
    generate_all_samples()

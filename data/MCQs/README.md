---
license: apache-2.0
task_categories:
- text-generation
language:
- en
---

# Dataset Card for NCERT_MCQs 🧠📘

## Summary
This dataset is curated for the task of generating Multiple Choice Questions (MCQs) from NCERT-based academic passages. It is designed to fine-tune Large Language Models (LLMs), particularly LLaMA 3.1, for educational question generation systems. The MCQs are structured into easy, medium, and hard categories following **Bloom’s Taxonomy**.

## Supported Tasks and Use Cases
- **Text-to-MCQ Generation**: Given an academic passage, the model generates MCQs.
- **Educational Assessment**: Useful for building AI-based Personalized Learning Assistants and intelligent tutoring systems.
- **Bloom-based Difficulty Classification**: Enables differentiated instruction and adaptive testing.

## Languages
The dataset is in **English**.

## Dataset Structure
Each record contains:
- `Passage`: The input academic text passage.
- `MCQs`: A list or string containing 15 MCQs generated from the passage.
- `Difficulty Level`: (Optional) Tag indicating whether questions are Easy, Medium, or Hard.
- `Answer Key`: Correct options for each question.

## Data Fields
| Column Name     | Description                                                |
|------------------|------------------------------------------------------------|
| `Passage`        | A paragraph or passage from NCERT textbooks                |
| `MCQs`           | Generated Multiple Choice Questions                        |
| `Difficulty Level` | (Optional) Easy / Medium / Hard tagging per Bloom’s Taxonomy |
| `Answer Key`     | The correct answers to each generated question             |

## Dataset Creation
The dataset was created using a mix of:
- NCERT textbook content (publicly available).
- Fine-tuned LLaMA 3.1 model trained using QLoRA.
- Custom prompting strategies to enforce Bloom’s Taxonomy in question generation.

## Intended Use
- Training and evaluating LLMs on the task of MCQ generation.
- Use in educational technologies for student assessment and curriculum design.
- Research in AI for Education (AIED), adaptive learning, and knowledge tracing.

## Limitations
- The dataset may not be exhaustive for all educational topics.
- Generated questions may occasionally contain hallucinations or formatting inconsistencies.
- Limited to NCERT-style content and may need generalization for other curricula.

## Licensing
This dataset is distributed under the **Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)** license.

## Citation
If you use this dataset, please cite:
@misc{ncertmcq2025,
title={NCERT MCQ Generation Dataset},
author={Goenka, Lokesh},
year={2025},
note={Fine-tuned on LLaMA 3.1 for educational assessment},
url={https://huggingface.co/datasets/goenkalokesh/NCERT_MCQs/}
}


## Contact
For questions or feedback, please contact: goenkalokesh@gmail.com
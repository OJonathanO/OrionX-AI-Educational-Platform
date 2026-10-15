"""Create sample educational documents and ingest them for testing.

Usage:
    python scripts/ingest_sample_documents.py [--user-id USER_ID]
"""
import argparse
import os
import sys
import tempfile
import uuid

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.database import SessionLocal
from app.models import Document, ProcessingStatus, User
from app.rag.ingestion import IngestionService
from app.rag.vector_store import InMemoryVectorStore, set_vector_store


SAMPLE_DOCUMENTS = [
    {
        "title": "Introduction to Calculus",
        "subject": "Mathematics",
        "content": """# Introduction to Calculus

Calculus is a branch of mathematics that deals with the study of rates of change and accumulation of quantities. It was independently developed by Isaac Newton and Gottfried Wilhelm Leibniz in the 17th century.

## Limits

A limit describes the value that a function approaches as the input approaches some value. Limits are essential to calculus and mathematical analysis.

The concept of a limit is fundamental to the definition of continuity, derivatives, and integrals.

## Derivatives

The derivative of a function measures the rate of change of the function value with respect to its input. It is often described as the "instantaneous rate of change."

The derivative of f(x) = x^2 is f'(x) = 2x. This means that at any point x, the slope of the tangent line to the curve is 2x.

## Integrals

Integration is the reverse process of differentiation. It is used to find areas under curves, volumes of solids, and many other quantities.

The definite integral of a function from a to b represents the signed area between the function and the x-axis.

## Applications

Calculus has widespread applications in:
- Physics: motion, forces, energy
- Engineering: optimization, signal processing
- Economics: marginal cost, marginal revenue
- Biology: population growth models
- Medicine: drug concentration over time
""",
    },
    {
        "title": "Newton's Laws of Motion",
        "subject": "Physics",
        "content": """# Newton's Laws of Motion

Newton's Laws of Motion are three fundamental laws that describe the relationship between a body and the forces acting upon it, and its motion in response to those forces.

## First Law: Inertia

An object at rest stays at rest, and an object in motion stays in motion with the same speed and in the same direction, unless acted upon by an unbalanced force.

This law is also known as the law of inertia. It means that objects resist changes to their state of motion.

## Second Law: F = ma

The acceleration of an object is directly proportional to the net force acting on it and inversely proportional to its mass.

F = ma, where F is the net force, m is the mass, and a is the acceleration.

This law explains how the velocity of an object changes when it is subjected to an external force.

## Third Law: Action and Reaction

For every action, there is an equal and opposite reaction.

When one body exerts a force on a second body, the second body simultaneously exerts a force equal in magnitude and opposite in direction on the first body.

## Examples

1. A book resting on a table: The table exerts an upward normal force equal to the book's weight.
2. A rocket launching: The exhaust gases push downward, and the rocket is pushed upward.
3. Walking: Your foot pushes backward on the ground, and the ground pushes you forward.

## Importance

These laws form the foundation of classical mechanics and are essential for understanding the motion of objects in our everyday lives and in the universe.
""",
    },
    {
        "title": "World War II Overview",
        "subject": "History",
        "content": """# World War II Overview

World War II (1939-1945) was a global war that involved most of the world's nations, including all of the great powers, eventually forming two opposing military alliances: the Allies and the Axis.

## Causes

The causes of World War II include:
- The Treaty of Versailles and its harsh terms on Germany
- The rise of fascism in Italy and Germany
- Japanese expansionism in Asia
- The failure of the League of Nations
- The Great Depression and its economic effects

## Major Events

### 1939: Invasion of Poland
Germany invaded Poland on September 1, 1939, triggering the start of the war.

### 1940: Battle of Britain
The German Luftwaffe attempted to gain air superiority over Britain but was repelled by the Royal Air Force.

### 1941: Operation Barbarossa
Germany launched a massive invasion of the Soviet Union, opening the Eastern Front.

### 1941: Pearl Harbor
Japan attacked the U.S. naval base at Pearl Harbor on December 7, 1941, bringing the United States into the war.

### 1944: D-Day
Allied forces landed in Normandy, France on June 6, 1944, beginning the liberation of Western Europe.

### 1945: End of the War
Germany surrendered in May 1945. Japan surrendered in August 1945 after atomic bombs were dropped on Hiroshima and Nagasaki.

## Consequences

- An estimated 70-85 million people died
- The United Nations was established
- The Cold War began between the United States and the Soviet Union
- Decolonization accelerated across Asia and Africa
- The State of Israel was established in 1948
""",
    },
    {
        "title": "Cell Biology Fundamentals",
        "subject": "Biology",
        "content": """# Cell Biology Fundamentals

Cells are the basic structural and functional units of all living organisms. They are the smallest units of life that can replicate independently.

## Cell Theory

Cell theory states:
1. All living organisms are composed of one or more cells
2. The cell is the basic unit of structure and organization in organisms
3. All cells arise from pre-existing cells

## Types of Cells

### Prokaryotic Cells
- Lack a nucleus and membrane-bound organelles
- Include bacteria and archaea
- Generally smaller and simpler

### Eukaryotic Cells
- Have a nucleus and membrane-bound organelles
- Include plants, animals, fungi, and protists
- More complex in structure

## Cell Organelles

### Nucleus
Contains the cell's genetic material (DNA) and controls cell activities.

### Mitochondria
The powerhouse of the cell. They generate most of the cell's ATP through cellular respiration.

### Ribosomes
Sites of protein synthesis. They read mRNA and assemble amino acids into proteins.

### Endoplasmic Reticulum
Rough ER has ribosomes and is involved in protein synthesis. Smooth ER is involved in lipid synthesis.

### Golgi Apparatus
Modifies, packages, and ships proteins and lipids to their destinations.

### Lysosomes
Contain digestive enzymes that break down waste materials and cellular debris.

### Cell Membrane
A phospholipid bilayer that controls what enters and exits the cell.

## Cellular Respiration

Cellular respiration is the process by which cells convert glucose into ATP:
1. Glycolysis (cytoplasm)
2. Krebs cycle (mitochondria)
3. Electron transport chain (mitochondria)

The overall equation: C6H12O6 + 6O2 → 6CO2 + 6H2O + ATP

## Photosynthesis

Photosynthesis occurs in plant chloroplasts:
6CO2 + 6H2O + light energy → C6H12O6 + 6O2

This process converts light energy into chemical energy stored in glucose.
""",
    },
]


def create_sample_documents(user_id: int):
    """Create sample documents and ingest them into the RAG pipeline."""
    db = SessionLocal()
    ingestion = IngestionService()

    created_docs = []
    for doc_data in SAMPLE_DOCUMENTS:
        document_id = uuid.uuid4().hex

        # Create a temporary text file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(doc_data["content"])
            temp_path = f.name

        try:
            # Process the document through the ingestion pipeline
            chunks, chunk_count = ingestion.process_document(
                file_path=temp_path,
                document_id=document_id,
                owner_id=user_id,
                title=doc_data["title"],
                file_type="txt",
            )

            # Create database record
            document = Document(
                id=document_id,
                owner_id=user_id,
                title=doc_data["title"],
                filename=f"{document_id}.txt",
                file_type="txt",
                file_size=len(doc_data["content"]),
                subject=doc_data["subject"],
                description=f"Sample document about {doc_data['title']}",
                extracted_text=doc_data["content"],
                processing_status=ProcessingStatus.completed,
                chunk_count=chunk_count,
                is_public=True,
            )
            db.add(document)
            created_docs.append(document)
            print(f"  Created: {doc_data['title']} ({chunk_count} chunks)")

        finally:
            os.unlink(temp_path)

    db.commit()
    db.close()
    return created_docs


def main():
    parser = argparse.ArgumentParser(description="Ingest sample educational documents for testing.")
    parser.add_argument("--user-id", type=int, default=1, help="User ID to own the documents")
    args = parser.parse_args()

    # Use in-memory vector store for sample ingestion
    set_vector_store(InMemoryVectorStore())

    print(f"Creating sample documents for user {args.user_id}...")
    docs = create_sample_documents(args.user_id)
    print(f"\nSuccessfully created {len(docs)} sample documents:")
    for doc in docs:
        print(f"  - {doc.title} ({doc.subject})")


if __name__ == "__main__":
    main()

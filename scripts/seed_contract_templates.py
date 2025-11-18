"""Seed contract templates into database with embeddings"""
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import List, Dict
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from hyperagent.models.template import ContractTemplate
from hyperagent.llm.provider import LLMProviderFactory
from hyperagent.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def seed_templates():
    """Seed contract templates from JSON files"""
    
    # Initialize database connection
    engine = create_async_engine(settings.database_url.replace("postgresql://", "postgresql+asyncpg://"))
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Initialize LLM provider for embeddings
    if not settings.gemini_api_key:
        logger.error("GEMINI_API_KEY not set. Cannot generate embeddings.")
        logger.error("Please set GEMINI_API_KEY in .env file")
        logger.error("Get your API key from: https://makersuite.google.com/app/apikey")
        logger.error("Or use OpenAI as fallback by setting OPENAI_API_KEY")
        sys.exit(1)
    
    llm_provider = LLMProviderFactory.create(
        "gemini",
        api_key=settings.gemini_api_key,
        model_name=settings.gemini_model
    )
    
    # Load templates from templates directory
    templates_dir = Path(__file__).parent.parent / "templates"
    if not templates_dir.exists():
        logger.warning(f"Templates directory not found: {templates_dir}")
        logger.info("Creating templates directory...")
        templates_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Please add template JSON files to templates/ directory")
        return
    
    template_files = list(templates_dir.glob("*.json"))
    if not template_files:
        logger.warning(f"No template files found in {templates_dir}")
        return
    
    logger.info(f"Found {len(template_files)} template files")
    
    async with async_session() as session:
        seeded_count = 0
        skipped_count = 0
        error_count = 0
        
        for template_file in template_files:
            try:
                # Load template JSON
                with open(template_file, 'r', encoding='utf-8') as f:
                    template_data = json.load(f)
                
                name = template_data.get("name")
                if not name:
                    logger.warning(f"Template file {template_file.name} missing 'name' field, skipping")
                    error_count += 1
                    continue
                
                # Check if template already exists
                from sqlalchemy import select
                result = await session.execute(
                    select(ContractTemplate).where(ContractTemplate.name == name)
                )
                existing = result.scalar_one_or_none()
                
                if existing:
                    logger.info(f"Template '{name}' already exists, skipping")
                    skipped_count += 1
                    continue
                
                # Generate embedding for template
                template_code = template_data.get("template_code", "")
                description = template_data.get("description", "")
                
                # Create embedding text (description + code snippet)
                embedding_text = f"{description}\n{template_code[:500]}"  # First 500 chars of code
                embedding = await llm_provider.embed(embedding_text)
                
                # Upload to IPFS if Pinata is configured
                ipfs_hash = template_data.get("ipfs_hash")
                if not ipfs_hash and settings.pinata_jwt:
                    try:
                        from hyperagent.rag.pinata_manager import PinataManager
                        pinata = PinataManager(settings.pinata_jwt)
                        upload_result = await pinata.upload_template_with_metadata(
                            name=f"{name}.sol",
                            content=template_code,
                            metadata={
                                "name": name,
                                "contract_type": template_data.get("contract_type", "Custom"),
                                "version": template_data.get("version", "1.0.0"),
                                "source": "official"
                            }
                        )
                        ipfs_hash = upload_result["ipfs_hash"]
                        logger.info(f"Uploaded '{name}' to IPFS: {ipfs_hash}")
                    except Exception as e:
                        logger.warning(f"IPFS upload failed for '{name}': {e}")
                        # Continue without IPFS hash
                
                # Create template record
                template = ContractTemplate(
                    name=name,
                    description=description,
                    contract_type=template_data.get("contract_type", "Custom"),
                    template_code=template_code,
                    ipfs_hash=ipfs_hash,
                    embedding=embedding,
                    version=template_data.get("version", "1.0.0"),
                    is_active=template_data.get("is_active", True),
                    tags=template_data.get("tags", [])
                )
                
                session.add(template)
                await session.commit()
                
                logger.info(f"Seeded template: {name}")
                seeded_count += 1
                
            except Exception as e:
                logger.error(f"Error seeding template from {template_file.name}: {e}", exc_info=True)
                await session.rollback()
                error_count += 1
        
        logger.info(f"Seeding complete: {seeded_count} seeded, {skipped_count} skipped, {error_count} errors")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_templates())


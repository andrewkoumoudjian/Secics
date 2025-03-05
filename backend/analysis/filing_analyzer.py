                "cik": filing_metadata.get("cik", "unknown"),
                "additional_info": company_info or {}
            },
            "filing_type": filing_type,
            "filing_date": filing_date,
            "summary": summary_result.get("analysis", ""),
            "section_analyses": section_analyses,
            "overall_assessment": assessment_result.get("analysis", ""),
            "analysis_timestamp": datetime.now().isoformat(),
            "metadata": {
                "original_metadata": filing_metadata,
                "analysis_success": summary_result.get("success", False) and assessment_result.get("success", False)
            }
        }

async def test_filing_analyzer():
    """Test the filing analyzer with a sample filing."""
    analyzer = FilingAnalyzer()
    
    # Example filing text and metadata
    sample_filing = """
    UNITED STATES
    SECURITIES AND EXCHANGE COMMISSION
    Washington, D.C. 20549
    
    FORM 8-K
    
    CURRENT REPORT
    Pursuant to Section 13 or 15(d) of The Securities Exchange Act of 1934
    
    Date of Report (Date of earliest event reported): March 1, 2023
    
    APPLE INC.
    (Exact name of Registrant as specified in its charter)
    
    California
    (State or Other Jurisdiction of Incorporation)
    
    Item 2.02 Results of Operations and Financial Condition.
    
    On January 27, 2023, Apple Inc. ("Apple") issued a press release regarding Apple's financial results for its first fiscal quarter ended December 24, 2022. A copy of Apple's press release is attached hereto as Exhibit 99.1.
    
    In the press release, Apple disclosed record quarterly revenue of $97.3 billion, up 9% year over year, and quarterly earnings per diluted share of $1.52.
    """
    
    sample_metadata = {
        "accession_number": "0000320193-23-000077",
        "company_name": "APPLE INC",
        "cik": "0000320193",
        "form_type": "8-K",
        "filing_date": "2023-03-01"
    }
    
    # Run the analysis
    analysis_result = await analyzer.analyze_filing(sample_filing, sample_metadata)
    
    # Print results
    print(f"Filing Summary: {analysis_result['summary'][:200]}...")
    print(f"Overall Assessment: {analysis_result['overall_assessment'][:200]}...")
    print(f"Number of section analyses: {len(analysis_result['section_analyses'])}")

if __name__ == "__main__":
    asyncio.run(test_filing_analyzer())
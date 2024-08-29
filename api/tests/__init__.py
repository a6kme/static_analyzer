import vcr

# Initialize the VCR
test_vcr = vcr.VCR(
    cassette_library_dir='cassettes/',  # Directory to store the cassettes
    record_mode='once',  # 'once' records the interactions and uses them if present
    # Criteria for matching requests to recorded interactions
    match_on=['uri', 'method'],
)

import hashlib

def dna_to_private_key(genome_sequence:str, salt:str) -> str:
    # genome never stored - only hash returned
    return hashlib.sha512((genome_sequence + salt).encode()).hexdigest()

def private_to_public_key(private:str) -> str:
    return hashlib.sha256(private.encode()).hexdigest()

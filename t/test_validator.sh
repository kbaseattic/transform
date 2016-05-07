#!/bin/sh

/kb/dev_container/modules/transform/plugins/scripts/validate/trns_validate_FASTA_DNA.py -i ./test-fasta/Sample1.fasta
/kb/dev_container/modules/transform/plugins/scripts/validate/trns_validate_FASTQ_DNA.py -i ./test-fastq/Sample1.fastq 
/kb/dev_container/modules/transform/plugins/scripts/validate/trns_validate_FASTQ_DNA.py -i ./test-fastq/Sample2_interleaved_illumina.fastq
/kb/dev_container/modules/transform/plugins/scripts/validate/trns_validate_FASTQ_DNA.py -i ./test-fastq/Sample3_interleaved_casava1.8.fastq
/kb/dev_container/modules/transform/plugins/scripts/validate/trns_validate_FASTQ_DNA.py -i ./test-fastq/Sample4_interleaved_NCBI_SRA.fastq
/kb/dev_container/modules/transform/plugins/scripts/validate/trns_validate_FASTQ_DNA.py -i ./test-fastq/Sample5_noninterleaved.1.fastq
/kb/dev_container/modules/transform/plugins/scripts/validate/trns_validate_FASTQ_DNA.py -i ./test-fastq/Sample5_noninterleaved.2.fastq

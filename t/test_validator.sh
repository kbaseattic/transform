#!/bin/sh

/kb/dev_container/modules/transform/scripts/trns_validate_KBaseAssembly.FA.py -i ./test-fasta/Sample1.fasta
/kb/dev_container/modules/transform/scripts/trns_validate_KBaseAssembly.FQ.py -i ./test-fastq/Sample1.fastq 
/kb/dev_container/modules/transform/scripts/trns_validate_KBaseAssembly.FQ.py -i ./test-fastq/Sample2_interleaved_illumina.fastq
/kb/dev_container/modules/transform/scripts/trns_validate_KBaseAssembly.FQ.py -i ./test-fastq/Sample3_interleaved_casava1.8.fastq

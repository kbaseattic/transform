package us.kbase.genbank.test;

import java.io.*;
import java.util.*;
import java.net.URL;

import java.nio.file.*;

import org.junit.Test;
import static junit.framework.Assert.*;

import org.strbio.IO;
import org.strbio.local.Program;
import org.strbio.util.*;
import com.fasterxml.jackson.databind.*;

import us.kbase.auth.AuthService;
import us.kbase.auth.AuthToken;
import us.kbase.common.service.*;
import us.kbase.workspace.*;
import us.kbase.kbasegenomes.*;
import us.kbase.genbank.*;

/**
   Unit tests of Genbank format
*/
public class FormatTest {
    private static final String testPath = "/kb/dev_container/modules/transform/t/genbank/";

    // ones in "nonstandard" directory should throw errors or warnings.
    private static final String[] sampleGBKs = { "NC_005213/NC_005213.gbk",
						 "NC_009925/NC_009925.gbk",
						 "standard/sample1.gbk",
						 "nonstandard/sample2.gbk",
						 "nonstandard/sample3.gbk",
						 "nonstandard/sample4.gbk",
						 "nonstandard/sample5.gbk",
						 "nonstandard/sample6.gbk" };

    /**
       check that we can read all files, and that the gold standard
       files will load as Genome/Contigset objects.
    */
    @Test public void testRead() throws Exception {
	ObjectMapper mapper = new ObjectMapper();

	Genome genome = null;
	ContigSet cs = null;
	File f = null;

	for (String g : sampleGBKs) {
	    byte[] b = Files.readAllBytes(Paths.get(testPath+g));
	    assertTrue(g+" should have more than 100 bytes",
		       b.length > 100);

	    try {
		g = StringUtil.replace(g,".gbk",".genome");
		f = new File(testPath+g);
		genome = mapper.readValue(f, Genome.class);

		g = StringUtil.replace(g,".genome",".contigset");
		f = new File(testPath+g);
		cs = mapper.readValue(f, ContigSet.class);
	    }
	    catch (Exception e) {
		if (!g.startsWith("nonstandard/"))
		    throw e;
	    }
	}
    }

    /**
       Check that standard files all match their objects
    */
    @Test public void testStandard() throws Exception {
	ObjectMapper mapper = new ObjectMapper();

	Genome genome = null;
	ContigSet cs = null;
	File f = null;
	List<File> files = null;

	for (String g : sampleGBKs) {
	    if (!g.startsWith("nonstandard/")) {
		files = new ArrayList<File>();
		f = new File(testPath+g);
		files.add(f);

		// null ws/id = don't really upload the results
		ArrayList ar = GbkUploader.uploadGbk(files,null,null,true);

		genome = (Genome)ar.get(2);
		cs = (ContigSet)ar.get(4);

		// compare to gold standards
		g = StringUtil.replace(g,".gbk",".genome");
		f = new File(testPath+g);
		Genome genomeGold = mapper.readValue(f, Genome.class);

		// pretty print diffs
		File f2 = File.createTempFile("obj",null);
		mapper.writeValue(f2,genome);
		String diffs = prettyDiffs(f,f2);
		f2.delete();
		assertTrue(diffs, diffs.length() == 0);

		g = StringUtil.replace(g,".genome",".contigset");
		f = new File(testPath+g);
		ContigSet csGold = mapper.readValue(f, ContigSet.class);

		f2 = File.createTempFile("obj",null);
		mapper.writeValue(f2,cs);
		diffs = prettyDiffs(f,f2);
		f2.delete();
		assertTrue(diffs, diffs.length() == 0);
	    }
	}
    }

    /**
       return a diff between the pretty-printed versions of two
       json objects.  Requires python -m json.tool and diff to
       be installed.
    */
    final public static String prettyDiffs(File a, File b) throws Exception {
	File fmtAFile = File.createTempFile("obj",null);
	fmtAFile.delete();
	File fmtBFile = File.createTempFile("obj",null);
	fmtBFile.delete();
	File diffFile = File.createTempFile("diff",null);
	diffFile.delete();

	// pretty print both input objects
	Program python = new Program("python");
	String[] inputs = new String[4];
	inputs[0] = "-m";
	inputs[1] = "json.tool";
	inputs[2] = a.getPath();
	inputs[3] = fmtAFile.getPath();

	python.setInput(null);
	python.setOutput(null);
	python.run(inputs);
	
	inputs[2] = b.getPath();
	inputs[3] = fmtBFile.getPath();
	python.run(inputs);

	// make diff
	Program diff = new Program("diff");
	inputs = new String[2];
	inputs[0] = fmtAFile.getPath();
	inputs[1] = fmtBFile.getPath();
	diff.setInput(null);
	OutputStream os = new FileOutputStream(diffFile);
	diff.setOutput(os);
	diff.run(inputs);
	os.close();

	// grab output
	byte[] rv = Files.readAllBytes(Paths.get(diffFile.getPath()));

	// clean up
	fmtAFile.delete();
	fmtBFile.delete();
	diffFile.delete();
	
	return new String(rv);
    }
}
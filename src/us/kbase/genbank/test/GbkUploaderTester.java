package us.kbase.genbank.test;

import java.io.BufferedReader;
import java.io.File;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.io.StringWriter;
import java.net.URL;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;

import com.fasterxml.jackson.databind.ObjectMapper;

import us.kbase.auth.AuthToken;
import us.kbase.common.service.Tuple11;
import us.kbase.common.service.UObject;
import us.kbase.genbank.GbkUploader;
import us.kbase.genbank.ObjectStorage;
import us.kbase.typedobj.core.TypeDefId;
import us.kbase.typedobj.core.TypeDefName;
import us.kbase.typedobj.core.TypedObjectValidationReport;
import us.kbase.typedobj.core.TypedObjectValidator;
import us.kbase.typedobj.db.FileTypeStorage;
import us.kbase.typedobj.db.TypeDefinitionDB;
import us.kbase.workspace.ObjectData;
import us.kbase.workspace.ObjectIdentity;
import us.kbase.workspace.SaveObjectsParams;
import us.kbase.workspace.WorkspaceClient;
import us.kbase.workspace.kbase.Util;

public class GbkUploaderTester {
	
	public static void main(String[] args) throws Exception {
		String spec = loadResourceFile(GbkUploaderTester.class.getResourceAsStream("KBaseGenomes.properties"));
		File typedbDir = new File("typedb");
		if (typedbDir.exists())
			deleteRecursively(typedbDir);
		typedbDir.mkdir();
		TypeDefinitionDB db = new TypeDefinitionDB(new FileTypeStorage(typedbDir.getAbsolutePath()), 
				new File("temp_files"), new Util().getKIDLpath(), "internal");
		List<String> types =  Arrays.asList("Genome","ContigSet");
		String moduleName = "KBaseGenomes";
		String username = "cshenry";

        //WHY NEED TO REGISTER A NEW MODULE?
		db.requestModuleRegistration(moduleName, username);
		db.approveModuleRegistrationRequest(username, moduleName, true);
		db.registerModule(spec, types, username);
		db.releaseModule(moduleName, username, false);

		final TypedObjectValidator validator = new TypedObjectValidator(db);
		
		Map<String, List<String>> genomeNameToPaths = new TreeMap<String, List<String>>();
		
		parseAllInDir(new int[] {1}, new File("."), new ObjectStorage() {
			@Override
			public List<Tuple11<Long, String, String, String, Long, String, Long, String, String, Long, Map<String, String>>> saveObjects(
					String authToken, SaveObjectsParams params) throws Exception {
				validateObject(validator, params.getObjects().get(0).getName(), 
						params.getObjects().get(0).getData(), params.getObjects().get(0).getType());
				return null;
			}
			@Override
			public List<ObjectData> getObjects(String authToken,
					List<ObjectIdentity> objectIds) throws Exception {
				throw new IllegalStateException("Unsupported method");
			}
		}, genomeNameToPaths);
		new ObjectMapper().writeValue(new File("genome2ftp.json"), genomeNameToPaths);
	}

	private static void validateObject(TypedObjectValidator validator, String objName, UObject obj, String type) throws Exception {
		TypedObjectValidationReport report = validator.validate(obj,new TypeDefId(new TypeDefName(type)));
		List <String> mssgs = report.getErrorMessages();
		for (int i = 0; i < mssgs.size(); i++) {
			System.out.println("    ["+i+"]:"+mssgs.get(i));
		}
		if (!report.isInstanceValid())
			throw new IllegalStateException("["+objName+"] does not validate");
	}
	
	public static void parseAllInDir(int[] pos, File dir, ObjectStorage wc, Map<String, List<String>> genomeNameToPaths) throws Exception {
		List<File> files = new ArrayList<File>();
		for (File f : dir.listFiles()) {
			if (f.isDirectory()) {
				parseAllInDir(pos, f, wc, genomeNameToPaths);
			} else if (f.getName().endsWith(".gbk")) {
				files.add(f);
			}
		}
		if (files.size() > 0)
			parseGenome(pos, dir, files, wc, genomeNameToPaths);

	}
	
	public static void parseGenome(int[] pos, File dir, List<File> gbkFiles, ObjectStorage wc, Map<String, List<String>> genomeNameToPaths) throws Exception {
		System.out.println("[" + (pos[0]++) + "] " + dir.getName());
		long time = System.currentTimeMillis();
		GbkUploader.uploadGbk(gbkFiles, wc, "", dir.getName(), "", genomeNameToPaths);

        //GbkUploader.uploadtoWS(wc, ws, id, token, genome, contigId, contigSet, meta);

		System.out.println("    time: " + (System.currentTimeMillis() - time) + " ms");
	}

	public static WorkspaceClient createWsClient(String token, String wsUrl) throws Exception {
		WorkspaceClient ret = new WorkspaceClient(new URL(wsUrl), new AuthToken(token));
		ret.setAuthAllowedForHttp(true);
		return ret;
	}
	
	private static String loadResourceFile(InputStream is) throws Exception {
		StringWriter sw = new StringWriter();
		PrintWriter pw = new PrintWriter(sw);
		if (is == null)
			throw new IllegalStateException("Resource not found");
		BufferedReader br = new BufferedReader(new InputStreamReader(is));
		while (true) {
			String line = br.readLine();
			if (line == null)
				break;
			pw.println(line);
		}
		br.close();
		pw.close();
		return sw.toString();
	}

	public static void deleteRecursively(File fileOrDir) {
		if (fileOrDir.isDirectory())
			for (File f : fileOrDir.listFiles()) 
				deleteRecursively(f);
		fileOrDir.delete();
	}
}

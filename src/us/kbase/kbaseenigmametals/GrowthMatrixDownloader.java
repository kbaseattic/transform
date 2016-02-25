package us.kbase.kbaseenigmametals;

import java.io.File;
import java.io.PrintWriter;
import java.net.URL;
import java.util.Arrays;
import java.util.List;

import org.apache.commons.cli.CommandLine;
import org.apache.commons.cli.CommandLineParser;
import org.apache.commons.cli.GnuParser;
import org.apache.commons.cli.HelpFormatter;
import org.apache.commons.cli.OptionBuilder;
import org.apache.commons.cli.Options;
import org.apache.commons.cli.ParseException;

import us.kbase.auth.AuthService;
import us.kbase.auth.AuthToken;
import us.kbase.kbaseenigmametals.GrowthMatrix;
import us.kbase.workspace.ObjectIdentity;
import us.kbase.workspace.WorkspaceClient;

public class GrowthMatrixDownloader {

	static Options options = new Options();
	static String wsUrl;
	static String wsName;
	static String objName;
	static Integer version;

	/**
	 * @param args
	 * @throws Exception
	 */
	public static void main(String[] args) throws Exception {
		MetadataProperties.startup();
		GrowthMatrixDownloader downloader = new GrowthMatrixDownloader();
		downloader.download(args);
	}

	public GrowthMatrixDownloader() {

		OptionBuilder.withLongOpt("help");
		OptionBuilder.withDescription("print this message");
		OptionBuilder.withArgName("help");
		options.addOption(OptionBuilder.create("h"));

		OptionBuilder.withLongOpt("test");
		OptionBuilder
				.withDescription("This option is for testing only. Program will exit without any output.");
		OptionBuilder.withArgName("test");
		options.addOption(OptionBuilder.create("t"));

		OptionBuilder.withLongOpt("workspace_service_url");
		OptionBuilder.withDescription("Workspace service URL");
		OptionBuilder.hasArg(true);
		OptionBuilder.withArgName("workspace_service_url");
		options.addOption(OptionBuilder.create("ws"));

		OptionBuilder.withLongOpt("workspace_name");
		OptionBuilder.withDescription("Workspace name");
		OptionBuilder.hasArg(true);
		OptionBuilder.withArgName("workspace_name");
		options.addOption(OptionBuilder.create("wn"));

		OptionBuilder.withLongOpt("object_name");
		OptionBuilder.withDescription("Object name");
		OptionBuilder.hasArg(true);
		OptionBuilder.withArgName("object_name");
		options.addOption(OptionBuilder.create("on"));

		OptionBuilder.withLongOpt("version");
		OptionBuilder.withDescription("Object version (optional)");
		OptionBuilder.hasOptionalArg();
		OptionBuilder.withArgName("version");
		options.addOption(OptionBuilder.create("ov"));

		OptionBuilder.withLongOpt("working_directory");
		OptionBuilder.withDescription("Working directory");
		OptionBuilder.hasArg(true);
		OptionBuilder.withArgName("working_directory");
		options.addOption(OptionBuilder.create("wd"));

		OptionBuilder.withLongOpt("output_file_name");
		OptionBuilder.withDescription("Output file name (optional)");
		OptionBuilder.hasOptionalArg();
		OptionBuilder.withArgName("output_file_name");
		options.addOption(OptionBuilder.create("of"));

	}

	public void download(String[] args) throws Exception {
		CommandLineParser parser = new GnuParser();

		try {
			// parse the command line arguments
			CommandLine line = parser.parse(options, args);
			if (line.hasOption("help")) {
				// automatically generate the help statement
				HelpFormatter formatter = new HelpFormatter();
				formatter
						.printHelp(
								"java -jar /kb/deployment/lib/jars/kbase/transform/kbase_transform_deps.jar [parameters]",
								options);

			} else if (line.hasOption("test")) {
				// return nothing and exit
				System.exit(0);
			} else {

				if (validateInput(line)) {

					wsUrl = line.getOptionValue("ws");
					wsName = line.getOptionValue("wn");
					objName = line.getOptionValue("on");
					if (line.hasOption("ov")){
						try {
							version = Integer.valueOf(line.getOptionValue("ov"));
						} catch (NumberFormatException e ){
							System.out.println("WARNING: version value not recognized");
							version = null;
						}
					}
					

			        String user = System.getenv("test.user");
			        String pwd = System.getenv("test.pwd");
			        
			        System.out.println(user);
			        System.out.println(pwd);
			        
			        String tokenString = System.getenv("KB_AUTH_TOKEN");
			        AuthToken token = tokenString == null ? AuthService.login(user, pwd).getToken() : new AuthToken(tokenString);

			        //get object
			        WorkspaceClient client = getWsClient(wsUrl, token);
		            String ref = wsName + "/" + objName;
		            if (version != null)
		                ref += "/" + version;

					GrowthMatrix matrix = client.getObjects(Arrays.asList(new ObjectIdentity().withRef(ref)))
		                    .get(0).getData().asClassInstance(GrowthMatrix.class);

					// System.out.println(matrix.toString());
					String outputFileName = line.getOptionValue("of");
			        if (outputFileName == null)
			            outputFileName = "growth.tsv";

			        String workDirName = line.getOptionValue("wd");
			        if (workDirName == null)
			            workDirName = (".");
			        File workDir = new File(workDirName);
			        if (!workDir.exists())
			            workDir.mkdirs();
			        File outputFile = new File(workDir, outputFileName);

			        generateTSV(new PrintWriter(outputFile), matrix);

				} else {
					HelpFormatter formatter = new HelpFormatter();
					formatter
							.printHelp(
									"java -jar /kb/deployment/lib/jars/kbase/enigma_metals/kbase-enigma-metals-0.1.jar [parameters]",
									options);
					System.exit(1);
				}
			}

		} catch (ParseException exp) {
			// oops, something went wrong
			System.err.println("Parsing failed.  Reason: " + exp.getMessage());
		}

	}

	private void generateTSV(PrintWriter pw, GrowthMatrix matrix) throws Exception {
		
		try {
			pw.print("DATA");
			for (String colName : matrix.getData().getColIds()){
				pw.print("\t" + colName);
			}
			pw.print("\n");
			int index = 0;
			for (String rowName : matrix.getData().getRowIds()){
				pw.print(rowName);
				for (int i = 0; i < matrix.getData().getColIds().size(); i++){
					Double value = matrix.getData().getValues().get(index).get(i);
					if (value != null){
						pw.print("\t" + value.toString());
					} else {
						pw.print("\t0");
					}
				}
				pw.print("\n");
				index++;
			}
			
			pw.print("METADATA\tCategory\tProperty\tUnit\tValue\n");
			for (PropertyValue value: matrix.getMetadata().getMatrixMetadata()){
				pw.print (printProperty("T", value));				
			}

			for (String colName : matrix.getData().getColIds()){
				List<PropertyValue> properties = matrix.getMetadata().getColumnMetadata().get(colName);
				for (PropertyValue value: properties){
					pw.print (printProperty(colName, value));
				}
			}
			
			for (String rowName : matrix.getData().getRowIds()){
				List<PropertyValue> properties = matrix.getMetadata().getRowMetadata().get(rowName);
				for (PropertyValue value: properties){
					pw.print (printProperty(rowName, value));
				}
			}
			
		} finally {
			pw.close();
		} 
		
	}

	private String printProperty(String id, PropertyValue value) {
		
		StringBuilder sb = new StringBuilder();
		sb.append(id);
		sb.append("\t");
		
		if (value.getCategory() != null) {
			sb.append(value.getCategory());
		}
		sb.append("\t");
		 
		if (value.getPropertyName() != null) {
			sb.append(value.getPropertyName());
		}
		sb.append("\t");

		if (value.getPropertyUnit() != null) {
			sb.append(value.getPropertyUnit());
		}
		sb.append("\t");

		if (value.getPropertyValue() != null) {
			sb.append(value.getPropertyValue());
		}
		sb.append("\n");

		return sb.toString();
	}

	private static boolean validateInput(CommandLine line) {
		boolean returnVal = true;
		if (!line.hasOption("ws")) {
			System.err.println("Workspace service URL required");
			returnVal = false;
		}

		if (!line.hasOption("wn")) {
			System.err.println("Workspace ID required");
			returnVal = false;
		}

		if (!line.hasOption("on")) {
			System.err.println("Object name required");
			returnVal = false;
		}

		if (!line.hasOption("wd")) {
			System.err.println("Working directory required");
			returnVal = false;
		}

		return returnVal;
	}

    private static WorkspaceClient getWsClient(String wsUrl, AuthToken token) throws Exception {
        WorkspaceClient wsClient = new WorkspaceClient(new URL(wsUrl), token);
        wsClient.setAuthAllowedForHttp(true);
        return wsClient;
    }


}

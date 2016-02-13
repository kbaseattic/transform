package us.kbase.kbaseenigmametals;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.apache.commons.cli.CommandLine;
import org.apache.commons.cli.CommandLineParser;
import org.apache.commons.cli.GnuParser;
import org.apache.commons.cli.HelpFormatter;
import org.apache.commons.cli.OptionBuilder;
import org.apache.commons.cli.Options;
import org.apache.commons.cli.ParseException;

import us.kbase.common.service.UObject;

public class ChromatographyMatrixUploader {

	static Options options = new Options();

	/**
	 * @param args
	 * @throws Exception
	 */
	public static void main(String[] args) throws Exception {
		MetadataProperties.startup();
		ChromatographyMatrixUploader uploader = new ChromatographyMatrixUploader();
		uploader.upload(args);
	}

	public ChromatographyMatrixUploader() {

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

		OptionBuilder.withLongOpt("input_directory");
		OptionBuilder.withDescription("Input directory");
		OptionBuilder.hasArg(true);
		OptionBuilder.withArgName("input_directory");
		options.addOption(OptionBuilder.create("id"));

		OptionBuilder.withLongOpt("working_directory");
		OptionBuilder.withDescription("Working directory");
		OptionBuilder.hasArg(true);
		OptionBuilder.withArgName("working_directory");
		options.addOption(OptionBuilder.create("wd"));

		OptionBuilder.withLongOpt("output_file_name");
		OptionBuilder.withDescription("Output file name");
		OptionBuilder.hasArg(true);
		OptionBuilder.withArgName("output_file_name");
		options.addOption(OptionBuilder.create("of"));

		OptionBuilder.withLongOpt("input_mapping");
		OptionBuilder.withDescription("Input mapping");
		OptionBuilder.hasArg(true);
		OptionBuilder.withArgName("input_mapping");
		options.addOption(OptionBuilder.create("im"));

		OptionBuilder.withLongOpt("format_type");
		OptionBuilder.withDescription("Format type");
		OptionBuilder.hasArg(true);
		OptionBuilder.withArgName("format_type");
		options.addOption(OptionBuilder.create("ft"));

	}
/*
	private static WorkspaceClient getWsClient(String wsUrl, AuthToken token)
			throws Exception {
		WorkspaceClient wsClient = new WorkspaceClient(new URL(wsUrl), token);
		wsClient.setAuthAllowedForHttp(true);
		return wsClient;
	}
*/
	public void upload(String[] args) throws Exception {
		CommandLineParser parser = new GnuParser();

		try {
			// parse the command line arguments
			CommandLine line = parser.parse(options, args);
			if (line.hasOption("help")) {
				// automatically generate the help statement
				HelpFormatter formatter = new HelpFormatter();
				formatter
						.printHelp(
								"java -cp /kb/deployment/lib/jars/kbase/enigma_metals/kbase-enigma-metals-0.1.jar [parameters]",
								options);

			} else if (line.hasOption("test")) {
				// return nothing and exit
				System.exit(0);
			} else {

				if (validateInput(line)) {

					File inputFile = findTabFile(new File(
							line.getOptionValue("id")));

					ChromatographyMatrix matrix = new ChromatographyMatrix();
					matrix.setName(line.getOptionValue("on"));

					matrix = generateChromatographyMatrix(inputFile, matrix);

					// System.out.println(matrix.toString());
					String outputFileName = line.getOptionValue("of");
			        if (outputFileName == null)
			            outputFileName = "matrix_output.json";

			        String workDirName = line.getOptionValue("wd");
			        if (workDirName == null)
			            workDirName = (".");
			        File workDir = new File(workDirName);
			        if (!workDir.exists())
			            workDir.mkdirs();
			        File outputFile = new File(workDir, outputFileName);
			        UObject.getMapper().writeValue(outputFile, matrix);

/*					WorkspaceClient cl = getWsClient(line.getOptionValue("ws"),
							token);
					List<ObjectSaveData> saveData = new ArrayList<ObjectSaveData>();
					saveData.add(new ObjectSaveData()
							.withData(
									UObject.transformObjectToObject(matrix,
											UObject.class))
							.withType("KBaseEnigmaMetals.GrowthMatrix")
							.withName(line.getOptionValue("on"))
							.withMeta(new HashMap<String, String>()));
					SaveObjectsParams params = new SaveObjectsParams()
							.withWorkspace(line.getOptionValue("wn"))
							.withObjects(saveData);

					cl.saveObjects(params);
*/
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

	public ChromatographyMatrix generateChromatographyMatrix(File inputFile, ChromatographyMatrix matrix)
			throws Exception {

		List<String> data = new ArrayList<String>();
		List<String> metaData = new ArrayList<String>();

		try {
			String line = null;
			int index = 0;
			boolean metaDataFlag = false;
			boolean dataFlag = false;
			BufferedReader br = new BufferedReader(new FileReader(inputFile));

			while ((line = br.readLine()) != null) {
				index++;
				if (line.equals("")) {
					// do nothing on blank lines
				} else if (line.matches("DATA\t.*")) {
					dataFlag = true;
					metaDataFlag = false;
					data.add(line);
				} else if (line.matches("METADATA\tCategory\tProperty\tUnit\tValue.*")) {
					dataFlag = false;
					metaDataFlag = true;
				} else {
					if (dataFlag && !metaDataFlag) {
						data.add(line);
					} else if (!dataFlag && metaDataFlag) {
						metaData.add(line);
					} else {
						System.out.println("Warning: line " + index + "will be missed");
					}
				}
			}
			br.close();
			if (!dataFlag && !metaDataFlag) {
				printErrorStatus("Data parsing");
				throw new IllegalStateException("Sorry, file format not recognized. Neither data nor metadata sections were found. Please check input file.");
			}
			
		} catch (IOException e) {
			System.err.println(e.getLocalizedMessage());
		}
		
		
		matrix.setData(DataMatrixUploader.parseData(data));
		
		matrix.setMetadata(parseChromatographyMetadata(metaData, matrix.getData().getColIds(), matrix.getData().getRowIds()));
		
		List<PropertyValue> properties = matrix.getMetadata().getMatrixMetadata();
		matrix.setDescription("");
		for (PropertyValue propertyValue:properties){
			if (propertyValue.getCategory().equals("Description")){
				matrix.setDescription(propertyValue.getPropertyValue());
				break;
			}
		}

		return matrix;
	}

	private Matrix2DMetadata parseChromatographyMetadata (List<String> metaData, List<String> sampleNames, List<String> rowNames) {
		
		Matrix2DMetadata returnVal = DataMatrixUploader.parseMetadata(metaData, sampleNames, rowNames, "3");//"3" is a dirty hack to avoid auto-generation of data series
		
		validateMetadata(returnVal, sampleNames, rowNames);

		return returnVal;
	};

	
	
	private void validateMetadata(Matrix2DMetadata m, List<String> columnNames, List<String> rowNames) {
		
		int flag = 0;
		int errorCount = 0;
		String timeUnit = "";
		
		for (String rowName : rowNames){
			flag = 0;
			try {
				for (PropertyValue p: m.getRowMetadata().get(rowName)){
					if (p.getCategory().equals(MetadataProperties.CHROMATOGRAPHYMATRIX_METADATA_ROW_TIMESERIES)){
						if (!MetadataProperties.GROWTHMATRIX_METADATA_ROW_TIMESERIES_TIME.contains(p.getPropertyName())) {
							if (errorCount == 0) printErrorStatus("Metadata validation");
							if (errorCount < 50) System.err.println(MetadataProperties.CHROMATOGRAPHYMATRIX_METADATA_ROW_TIMESERIES + " metadata entry for row " + rowName + " contains illegal property name " + p.getPropertyName());
							errorCount ++;
						}
						
						if (timeUnit.equals("")) timeUnit = p.getPropertyUnit();
						if (!MetadataProperties.GROWTHMATRIX_METADATA_ROW_TIMESERIES_TIME_UNIT.contains(p.getPropertyUnit())){
							if (errorCount == 0) printErrorStatus("Metadata validation");
							if (errorCount < 50) System.err.println(MetadataProperties.CHROMATOGRAPHYMATRIX_METADATA_ROW_TIMESERIES + "_" + p.getPropertyName() + " metadata entry for row " + rowName + " contains illegal unit " + p.getPropertyUnit());
							errorCount ++;
						} else if (!p.getPropertyUnit().equals(timeUnit)) {
							if (errorCount == 0) printErrorStatus("Metadata validation");
							if (errorCount < 50) System.err.println(MetadataProperties.CHROMATOGRAPHYMATRIX_METADATA_ROW_TIMESERIES + "_" + p.getPropertyName() + " metadata entry for row " + rowName + " contains unit " + p.getPropertyUnit() + ", which is different from " + timeUnit + " in other entries" );
							errorCount ++;
						}
						flag++;
						
					}
				}
			} catch (NullPointerException e) {
				if (errorCount == 0) printErrorStatus("Metadata validation");
				if (errorCount < 50) System.err.println("Metadata entries for row " + rowName + " are missing");
				errorCount ++;
			}
			if (flag == 0) {
				if (errorCount == 0) printErrorStatus("Metadata validation");
				if (errorCount < 50) System.err.println("Metadata for row " + rowName + " must have one " + MetadataProperties.CHROMATOGRAPHYMATRIX_METADATA_ROW_TIMESERIES + " entry");
				errorCount ++;
			} else if (flag > 1) {
				if (errorCount == 0) printErrorStatus("Metadata validation");
				if (errorCount < 50) System.err.println("Metadata for row " + rowName + " must have only one " + MetadataProperties.CHROMATOGRAPHYMATRIX_METADATA_ROW_TIMESERIES + " entry, but it contains " + flag);
				errorCount ++;
			}
		}

		
		Map<String,String> units = new HashMap<String, String>();
		
		for (String colName : columnNames) {
			boolean measurementFlag = false;
			
			try {
				for (PropertyValue p : m.getColumnMetadata().get(colName)){
					if (p.getCategory().equals(MetadataProperties.CHROMATOGRAPHYMATRIX_METADATA_COLUMN_MEASUREMENT)) {
						measurementFlag = true;
						if (p.getPropertyName().equals(MetadataProperties.CHROMATOGRAPHYMATRIX_METADATA_COLUMN_MEASUREMENT_INTENSITY)){
							if (MetadataProperties.CHROMATOGRAPHYMATRIX_METADATA_COLUMN_MEASUREMENT_INTENSITY_UNIT.contains(p.getPropertyUnit())){
								String key = p.getCategory() + p.getPropertyName() + p.getPropertyValue();
								if (units.containsKey(key)) {
									if (!units.get(key).equals(p.getPropertyUnit())) {
										if (errorCount == 0) printErrorStatus("Metadata validation");
										if (errorCount < 50) System.err.println(p.getCategory() + "_" + p.getPropertyName() + " metadata entry for column " + colName + " contains unit " + p.getPropertyUnit() + ", which is different from " + units.get(key) + " in other entries" );
										errorCount ++;
									}
								} else {
									units.put(key, p.getPropertyUnit());
								}
							} else {
								if (errorCount == 0) printErrorStatus("Metadata validation");
								if (errorCount < 50) System.err.println(p.getCategory() + "_" + p.getPropertyName() + " metadata entry for column " + colName + " contains illegal unit " + p.getPropertyUnit() );
								errorCount ++;
							}
						}
					}
				}
				if (!measurementFlag) {
					if (errorCount == 0) printErrorStatus("Metadata validation");
					if (errorCount < 50) System.err.println("Metadata for column " + colName + " must have at least one " + MetadataProperties.CHROMATOGRAPHYMATRIX_METADATA_COLUMN_MEASUREMENT + " entry");
					errorCount ++;
				}
			} catch (NullPointerException e) {
				if (errorCount == 0) printErrorStatus("Metadata validation");
				if (errorCount < 50) System.err.println("Metadata entries for column " + colName + " are missing");
				errorCount ++;
			}
		}
		
		if (errorCount > 50) {
			throw new IllegalStateException("Cannot proceed with upload: metadata validation failed. " + errorCount + " errors were found, but only first 50 were displayed");
		} else if (errorCount > 0) {
			throw new IllegalStateException("Cannot proceed with upload: metadata validation failed.");
		}

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

		if (!line.hasOption("id")) {
			System.err.println("Input directory required");
			returnVal = false;
		}

		if (!line.hasOption("wd")) {
			System.err.println("Working directory required");
			returnVal = false;
		}

		return returnVal;
	}

	private static void printErrorStatus(String message) {
		System.err.println("\n" + message + " failed. See detailed report for a list of errors.\n                                                                                                                                \n");
	}

	public static File findTabFile(File inputDir) {
		File inputFile = null;
		StringBuilder fileList = new StringBuilder();
		for (File f : inputDir.listFiles()) {
			if (!f.isFile())
				continue;
			String fileName = f.getName().toLowerCase();
			if (fileName.endsWith(".txt") || fileName.endsWith(".tsv")
					|| fileName.endsWith(".csv") || fileName.endsWith(".tab")) {
				inputFile = f;
				break;
			}
			if (fileList.length() > 0)
				fileList.append(", ");
			fileList.append(f.getName());
		}
		if (inputFile == null)
			throw new IllegalStateException(
					"Input file with extention .txt or .tsv was not "
							+ "found among: " + fileList);
		return inputFile;
	}

}

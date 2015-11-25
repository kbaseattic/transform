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

import us.kbase.kbaseenigmametals.FloatMatrix2D;
import us.kbase.kbaseenigmametals.DataMatrix;
import us.kbase.kbaseenigmametals.Matrix2DMetadata;;

public class DataMatrixUploader {

	protected static final String GROWTH_EXTERNAL_TYPE = "tsv.growth";
	protected static final String CHROMATOGRAPHY_EXTERNAL_TYPE = "tsv.chromatography";
	protected static final String WELLS_EXTERNAL_TYPE = "tsv.wells";
	
	static Options options = new Options();

	/**
	 * @param args
	 * @throws Exception
	 */
	public static void main(String[] args) throws Exception {
		DataMatrixUploader uploader = new DataMatrixUploader();
		uploader.upload(args);
	}

	public DataMatrixUploader() {


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

		OptionBuilder.withLongOpt("external_type");
		OptionBuilder.withDescription("External type");
		OptionBuilder.hasArg(true);
		OptionBuilder.withArgName("external_type");
		options.addOption(OptionBuilder.create("et"));

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
								"java -jar /kb/deployment/lib/jars/kbase/enigma_metals/kbase-enigma-metals-0.2.jar [parameters]",
								options);

			} else if (line.hasOption("test")) {
				// return nothing and exit
				System.exit(0);
			} else {

				if (validateInput(line)) {

					String externalType = line.getOptionValue("et");

					if (externalType.equalsIgnoreCase(GROWTH_EXTERNAL_TYPE)) {
						GrowthMatrixUploader uploader = new GrowthMatrixUploader();
						uploader.upload(args);
					} else if (externalType.equalsIgnoreCase(CHROMATOGRAPHY_EXTERNAL_TYPE)){
						ChromatographyMatrixUploader uploader = new ChromatographyMatrixUploader();
						uploader.upload(args);
					} else if (externalType.equalsIgnoreCase(WELLS_EXTERNAL_TYPE)){
						WellSampleMatrixUploader uploader = new WellSampleMatrixUploader();
						uploader.upload(args);
					} else {
						System.err.println("Unknown external type " + externalType);
						System.exit(1);
					};

				} else {
					HelpFormatter formatter = new HelpFormatter();
					formatter
							.printHelp(
									"java -jar /kb/deployment/lib/jars/kbase/enigma_metals/kbase-enigma-metals-0.2.jar [parameters]",
									options);
					System.exit(1);
				}
			}

		} catch (ParseException exp) {
			// oops, something went wrong
			System.err.println("Parsing failed.  Reason: " + exp.getMessage());
		}

	}

	public DataMatrix generateDataMatrix(File inputFile, DataMatrix matrix)
			throws Exception {

		List<String> data = new ArrayList<String>();
		List<String> metaData = new ArrayList<String>();

		try {
			String line = null;
			boolean metaDataFlag = false;
			boolean dataFlag = false;
			BufferedReader br = new BufferedReader(new FileReader(inputFile));
			while ((line = br.readLine()) != null) {
				if (line.equals("")) {
					// do nothing on blank lines
				} else if (line.matches("DATA\t\t.*")) {
					dataFlag = true;
					metaDataFlag = false;
				} else if (line.matches("METADATA\tEntity\tProperty\tUnit\tValue.*")) {
					dataFlag = false;
					metaDataFlag = true;
				} else {
					if (dataFlag && !metaDataFlag) {
						data.add(line);
					} else if (!dataFlag && metaDataFlag) {
						metaData.add(line);
					} else {
						System.out.println("Warning: string will be missed "
								+ line);
					}
					;
				}
				;

			}
			br.close();
		} catch (IOException e) {
			System.out.println(e.getLocalizedMessage());
		}
		
		matrix.setData(parseData(data));
		matrix.setMetadata(parseMetadata(metaData, matrix.getData().getColIds(), matrix.getData().getRowIds()));
		
		List<PropertyValue> properties = matrix.getMetadata().getMatrixMetadata();
		matrix.setDescription("");
		for (PropertyValue propertyValue:properties){
			if (propertyValue.getEntity().equals("Description")){
				matrix.setDescription(propertyValue.getPropertyValue());
				break;
			}
		}

		return matrix;
	}

	protected static FloatMatrix2D parseData(List<String> data) {
		List<List<Double>> dataValues = new ArrayList<List<Double>>();
		Long samplesNumber = 0L;
		List<String> sampleNames = new ArrayList<String>();
		List<String> rowNames = new ArrayList<String>();
		FloatMatrix2D floatMatrix = new FloatMatrix2D();

		for (String line : data) {
			if (line.matches("DATA\t.*")) {
				String[] fields = line.split("\t");
				for (int i = 1; i < fields.length; i++) {
					if (!fields[i].equals("")){
						sampleNames.add(fields[i]);
						samplesNumber ++;
					};
						//System.out.println(fields[i]);
				};
				/*
				 * for (Integer i = 0; i < samplesNumber; i++) { HashMap<String,
				 * Double> dataValue = new HashMap<String, Double>();
				 * dataValues.add(dataValue); }
				 */
			} else {
				// System.out.println(samplesNumber);
				//System.out.println(line);
				String[] fields = line.split("\t", -1);
				rowNames.add(fields[0]);

				List<Double> rowValues = new ArrayList<Double>();
				// System.out.println(fields.length);
				Integer j = 0;
				while (j < samplesNumber) {
					try {
						Double value = Double.valueOf(fields[j + 1]);
						rowValues.add(value);
					} catch (NumberFormatException e) {
						rowValues.add(0.00);
						System.out.println("WARNING: unsuccessful conversion of data value " + fields[j+1] + " in line " + line);
					}
					// System.out.println(fields[0]+" "+fields[j+1]);
					j++;
				}
				dataValues.add(rowValues);
			}
		}
		floatMatrix.setValues(dataValues);
		floatMatrix.setRowIds(rowNames);
		floatMatrix.setColIds(sampleNames);

		return floatMatrix;

	};

	protected static Matrix2DMetadata parseMetadata (List<String> columnMetadataLines, List<String> rowMetadataLines, List<String> sampleNames, List<String> rowNames) {
		Matrix2DMetadata returnVal = new Matrix2DMetadata();
		
		
		Map<String, List<PropertyValue>> columnMetadata = new HashMap<String, List<PropertyValue>>();
		Map<String, List<PropertyValue>> rowMetadata = new HashMap<String, List<PropertyValue>>();
		List<PropertyValue> matrixMetadata = new ArrayList<PropertyValue>();
		
		for (String line : columnMetadataLines) {
			if (line.equals("")) {
				// do nothing on blank lines
			} else {
				String[] fields = line.split("\t");
				if (fields[0].equals("T")) {
					// process series-specific fields
					PropertyValue propertyValue = new PropertyValue();
					if (fields.length > 1) propertyValue.setEntity(fields[1]);
					if (fields.length > 2) propertyValue.setPropertyName(fields[2]);
					if (fields.length > 3) propertyValue.setPropertyUnit(fields[3]);
					if (fields.length > 4) propertyValue.setPropertyValue(fields[4]);
					matrixMetadata.add(propertyValue);
				} else if (sampleNames.contains(fields[0])) {
					// process sample-specific fields
					PropertyValue propertyValue = new PropertyValue();
					if (fields.length > 1) propertyValue.setEntity(fields[1]);
					if (fields.length > 2) propertyValue.setPropertyName(fields[2]);
					if (fields.length > 3) propertyValue.setPropertyUnit(fields[3]);
					if (fields.length > 4) propertyValue.setPropertyValue(fields[4]);

					if (columnMetadata.containsKey(fields[0])) {
						List<PropertyValue> propertyValuesList = columnMetadata.get(fields[0]);
						propertyValuesList.add(propertyValue);
						columnMetadata.put(fields[0], propertyValuesList);
					} else {
						List<PropertyValue> propertyValuesList = new ArrayList<PropertyValue>();
						propertyValuesList.add(propertyValue);
						columnMetadata.put(fields[0], propertyValuesList);
					}
					
				} else {
					System.err.println("Unknown column label in line " + line);
				}
			}
		}

		for (String line : rowMetadataLines) {
			if (line.equals("")) {
				// do nothing on blank lines
			} else {
				String[] fields = line.split("\t");
				if (fields[0].equals("T")) {
					// process series-specific fields
					PropertyValue propertyValue = new PropertyValue();
					if (fields.length > 1) propertyValue.setEntity(fields[1]);
					if (fields.length > 2) propertyValue.setPropertyName(fields[2]);
					if (fields.length > 3) propertyValue.setPropertyUnit(fields[3]);
					if (fields.length > 4) propertyValue.setPropertyValue(fields[4]);
					matrixMetadata.add(propertyValue);
				} else if (rowNames.contains(fields[0])) {
					// process sample-specific fields
					PropertyValue propertyValue = new PropertyValue();
					if (fields.length > 1) propertyValue.setEntity(fields[1]);
					if (fields.length > 2) propertyValue.setPropertyName(fields[2]);
					if (fields.length > 3) propertyValue.setPropertyUnit(fields[3]);
					if (fields.length > 4) propertyValue.setPropertyValue(fields[4]);

					if (rowMetadata.containsKey(fields[0])) {
						List<PropertyValue> propertyValuesList = rowMetadata.get(fields[0]);
						propertyValuesList.add(propertyValue);
						rowMetadata.put(fields[0], propertyValuesList);
					} else {
						List<PropertyValue> propertyValuesList = new ArrayList<PropertyValue>();
						propertyValuesList.add(propertyValue);
						rowMetadata.put(fields[0], propertyValuesList);
					}
					
				} else {
					System.err.println("Unknown column label in line " + line);
				}
			}
		}

		returnVal.setColumnMetadata(columnMetadata);
		returnVal.setRowMetadata(rowMetadata);
		returnVal.setMatrixMetadata(matrixMetadata);
		
		return returnVal;
	};

	protected static Matrix2DMetadata parseMetadata (List<String> metadataLines, List<String> sampleNames, List<String> rowNames) {
		Matrix2DMetadata returnVal = new Matrix2DMetadata();
		
		Map<String, List<PropertyValue>> columnMetadata = new HashMap<String, List<PropertyValue>>();
		Map<String, List<PropertyValue>> rowMetadata = new HashMap<String, List<PropertyValue>>();
		List<PropertyValue> matrixMetadata = new ArrayList<PropertyValue>();
		
		for (String line : metadataLines) {
			if (line.equals("")) {
				// do nothing on blank lines
			} else {
				String[] fields = line.split("\t");
				if (fields[0].equals("T")) {
					// process series-specific fields
					PropertyValue propertyValue = new PropertyValue();
					if (fields.length > 1) propertyValue.setEntity(fields[1]);
					if (fields.length > 2) propertyValue.setPropertyName(fields[2]);
					if (fields.length > 3) propertyValue.setPropertyUnit(fields[3]);
					if (fields.length > 4) propertyValue.setPropertyValue(fields[4]);
					matrixMetadata.add(propertyValue);
				} else if (sampleNames.contains(fields[0])) {
					// process sample-specific fields
					PropertyValue propertyValue = new PropertyValue();
					if (fields.length > 1) propertyValue.setEntity(fields[1]);
					if (fields.length > 2) propertyValue.setPropertyName(fields[2]);
					if (fields.length > 3) propertyValue.setPropertyUnit(fields[3]);
					if (fields.length > 4) propertyValue.setPropertyValue(fields[4]);

					if (columnMetadata.containsKey(fields[0])) {
						List<PropertyValue> propertyValuesList = columnMetadata.get(fields[0]);
						propertyValuesList.add(propertyValue);
						columnMetadata.put(fields[0], propertyValuesList);
					} else {
						List<PropertyValue> propertyValuesList = new ArrayList<PropertyValue>();
						propertyValuesList.add(propertyValue);
						columnMetadata.put(fields[0], propertyValuesList);
					}
				} else if (rowNames.contains(fields[0])) {
					// process sample-specific fields
					PropertyValue propertyValue = new PropertyValue();
					if (fields.length > 1) propertyValue.setEntity(fields[1]);
					if (fields.length > 2) propertyValue.setPropertyName(fields[2]);
					if (fields.length > 3) propertyValue.setPropertyUnit(fields[3]);
					if (fields.length > 4) propertyValue.setPropertyValue(fields[4]);

					if (rowMetadata.containsKey(fields[0])) {
						List<PropertyValue> propertyValuesList = rowMetadata.get(fields[0]);
						propertyValuesList.add(propertyValue);
						rowMetadata.put(fields[0], propertyValuesList);
					} else {
						List<PropertyValue> propertyValuesList = new ArrayList<PropertyValue>();
						propertyValuesList.add(propertyValue);
						rowMetadata.put(fields[0], propertyValuesList);
					}
				} else {
					System.err.println("Unknown column label in line " + line);
				}
			}
		}

		returnVal.setColumnMetadata(columnMetadata);
		returnVal.setRowMetadata(rowMetadata);
		returnVal.setMatrixMetadata(matrixMetadata);
		
		return returnVal;
	};

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

		if (!line.hasOption("wd")) {
			System.err.println("External type required (for example, TSV.Growth)");
			returnVal = false;
		}

		return returnVal;
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

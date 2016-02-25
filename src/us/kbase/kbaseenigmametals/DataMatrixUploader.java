package us.kbase.kbaseenigmametals;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.Hashtable;
import java.util.List;
import java.util.Map;
import java.util.Vector;
import java.util.Map.Entry;

import org.apache.commons.cli.CommandLine;
import org.apache.commons.cli.CommandLineParser;
import org.apache.commons.cli.GnuParser;
import org.apache.commons.cli.HelpFormatter;
import org.apache.commons.cli.OptionBuilder;
import org.apache.commons.cli.Options;
import org.apache.commons.cli.ParseException;
import org.apache.commons.lang3.StringUtils;


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
		MetadataProperties.startup();
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
						SamplePropertyMatrixUploader uploader = new SamplePropertyMatrixUploader();
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
			int index = 0;
			while ((line = br.readLine()) != null) {
				index++;
				if (line.equals("")) {
					// do nothing on blank lines
				} else if (line.matches("DATA\t\t.*")) {
					dataFlag = true;
					metaDataFlag = false;
				} else if (line.matches("METADATA\tCategory\tProperty\tUnit\tValue.*")) {
					dataFlag = false;
					metaDataFlag = true;
				} else {
					if (dataFlag && !metaDataFlag) {
						data.add(line);
					} else if (!dataFlag && metaDataFlag) {
						metaData.add(line);
					} else {
						System.out.println("Warning: line " + index + " will be missed:\n"
								+ line);
					}
				}
			}
			br.close();
			
			if (!dataFlag && !metaDataFlag) {
				throw new IllegalStateException("Sorry, format not recognized. Check input file.");
			}

		} catch (IOException e) {
			System.out.println(e.getLocalizedMessage());
		}
		
		matrix.setData(parseData(data));
		matrix.setMetadata(parseMetadata(metaData, matrix.getData().getColIds(), matrix.getData().getRowIds(), "3"));//"3" is a dirty hack to avoid auto-generation of data series
		
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

	protected static FloatMatrix2D parseData(List<String> data) {
		List<List<Double>> dataValues = new ArrayList<List<Double>>();
		Long samplesNumber = 0L;
		List<String> sampleNames = new ArrayList<String>();
		List<String> rowNames = new ArrayList<String>();
		FloatMatrix2D floatMatrix = new FloatMatrix2D();
		int index = 0;

		for (String line : data) {
			index++;
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
				
				if (fields.length < samplesNumber + 1) {
					printErrorStatus("Data parsing");
					System.err.println("Data parsing failed: insufficient number of values in line " + index + " of data section");
					throw new IllegalStateException("Number of values in line " + index + " of the DATA section smaller than number of columns");
					
				}
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
						System.out.println("WARNING: unsuccessful conversion of data value " + fields[j+1] + " in row " + fields [0] + ", column " + j);
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
		
		boolean errorFlag = false;
		for (String line : columnMetadataLines) {
			if (line.equals("")) {
				// do nothing on blank lines
			} else {
				String[] fields = line.split("\t");
				if (fields[0].equals("T")) {
					// process series-specific fields
					PropertyValue propertyValue = new PropertyValue();
					if (fields.length > 1) propertyValue.setCategory(fields[1]);
					if (fields.length > 2) propertyValue.setPropertyName(fields[2]);
					if (fields.length > 3) propertyValue.setPropertyUnit(fields[3]);
					if (fields.length > 4) propertyValue.setPropertyValue(fields[4]);
					matrixMetadata.add(propertyValue);
				} else if (sampleNames.contains(fields[0])) {
					// process sample-specific fields
					PropertyValue propertyValue = new PropertyValue();
					if (fields.length > 1) propertyValue.setCategory(fields[1]);
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
					if (!errorFlag) printErrorStatus("Metadata parsing");
					System.err.println("Unknown column label " + fields[0] + " in the Metadata section.\n");
					errorFlag = true;
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
					if (fields.length > 1) propertyValue.setCategory(fields[1]);
					if (fields.length > 2) propertyValue.setPropertyName(fields[2]);
					if (fields.length > 3) propertyValue.setPropertyUnit(fields[3]);
					if (fields.length > 4) propertyValue.setPropertyValue(fields[4]);
					matrixMetadata.add(propertyValue);
				} else if (rowNames.contains(fields[0])) {
					// process sample-specific fields
					PropertyValue propertyValue = new PropertyValue();
					if (fields.length > 1) propertyValue.setCategory(fields[1]);
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
					if (!errorFlag) printErrorStatus("Metadata parsing");
					System.err.println("Unknown row label " + fields[0] + " in the Metadata section.\n");
					errorFlag = true;
				}
			}
		}

		if (errorFlag) {
			throw new IllegalStateException("Cannot proceed with upload: metadata parsing failed");
		}
		
		returnVal.setColumnMetadata(columnMetadata);
		returnVal.setRowMetadata(rowMetadata);
		returnVal.setMatrixMetadata(matrixMetadata);
		
		return returnVal;
	};

	protected static Matrix2DMetadata parseMetadata (List<String> metadataLines, List<String> sampleNames, List<String> rowNames, String repOption) {
		
		boolean errorFlag = false;
		boolean statValues = false;
		Matrix2DMetadata returnVal = new Matrix2DMetadata();
		
		Map<String, List<PropertyValue>> columnMetadata = new HashMap<String, List<PropertyValue>>();
		Map<String, List<PropertyValue>> rowMetadata = new HashMap<String, List<PropertyValue>>();
		List<PropertyValue> matrixMetadata = new ArrayList<PropertyValue>();
		int index = 0;
		
		for (String line : metadataLines) {
			index++;
			if (line.equals("")) {
				// do nothing on blank lines
			} else {
				String[] fields = line.split("\t");
				if (fields[0].equals("T")) {
					// process series-specific fields
					PropertyValue propertyValue = new PropertyValue();
					if (fields.length > 1) propertyValue.setCategory(fields[1]);
					if (fields.length > 2) propertyValue.setPropertyName(fields[2]);
					if (fields.length > 3) propertyValue.setPropertyUnit(fields[3]);
					if (fields.length > 4) propertyValue.setPropertyValue(fields[4]);
					matrixMetadata.add(propertyValue);
					
					if (propertyValue.getCategory().equals(MetadataProperties.DATAMATRIX_METADATA_TABLE_MEASUREMENT) && propertyValue.getPropertyName().equals(MetadataProperties.DATAMATRIX_METADATA_TABLE_MEASUREMENT_VALUES) && propertyValue.getPropertyValue().equals(MetadataProperties.DATAMATRIX_METADATA_TABLE_MEASUREMENT_VALUES_VALUE_STATVALUES)) {
						statValues = true;
					}

				} else if (sampleNames.contains(fields[0])) {
					// process sample-specific fields
					PropertyValue propertyValue = new PropertyValue();
					if (fields.length > 1) propertyValue.setCategory(fields[1]);
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
					if (fields.length > 1) propertyValue.setCategory(fields[1]);
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
					if (!errorFlag) printErrorStatus("Metadata parsing");
					System.err.println("Unknown column or row label " + fields[0] + " in line " + index + " of Metadata section");
					errorFlag = true;
					
				}
			}
		}
		
		if (errorFlag) {
			throw new IllegalStateException("Cannot proceed with upload: metadata parsing failed");
		}

//auto-generate data series IDs if not provided by user 
		if (repOption.equals("1") && !statValues) {
			generateSeriesIds(columnMetadata, MetadataProperties.GROWTHMATRIX_METADATA_COLUMN_CONDITION);
		} else if (repOption.equals("2") && !statValues) {
			int seriesIndex = 0; 
			for(Entry<String, List<PropertyValue>> entry: columnMetadata.entrySet()){
				seriesIndex++;
				entry.getValue().add(
						new PropertyValue()
						.withCategory(MetadataProperties.DATAMATRIX_METADATA_COLUMN_DATASERIES)
						.withPropertyName(MetadataProperties.DATAMATRIX_METADATA_COLUMN_DATASERIES_SERIESID)
						.withPropertyUnit("")
						.withPropertyValue("S" + seriesIndex)); 
			}
		}
		
		returnVal.setColumnMetadata(columnMetadata);
		returnVal.setRowMetadata(rowMetadata);
		returnVal.setMatrixMetadata(matrixMetadata);
		
		validateMetadata(returnVal, sampleNames, rowNames);
		
		return returnVal;
	};
	
	private static void generateSeriesIds(Map<String, List<PropertyValue>> columnMetadata, String category){
		Map<String, List<String>> columnProperties2columnIds = new Hashtable<String, List<String>>();
		List<String> columnProperties = new Vector<String>();
		
		// Build an association between concatenated properties and columnIds
		for(Entry<String, List<PropertyValue>> entry: columnMetadata.entrySet()){
			String columnId = entry.getKey();
			columnProperties.clear();
			
			// Build a list of properties
			for(PropertyValue pv: entry.getValue()){
				if(pv.getCategory().equals(category)){
					String property = pv.getPropertyName() + "." + pv.getPropertyUnit() + "." + pv.getPropertyValue();
					columnProperties.add(property);
				}
			}	
			
			// Sort properties alphabetically
			Collections.sort(columnProperties);
			String seriesProxyId = StringUtils.join(columnProperties, ";");
			
			// Register association between concatenated properties and column Id
			List<String> columnIds  = columnProperties2columnIds.get(seriesProxyId);
			if(columnIds == null){
				columnIds = new Vector<String>();
				columnProperties2columnIds.put(seriesProxyId, columnIds);
			}
			columnIds.add(columnId);						
		}
		
		// Generate Series Id, and build a  hash to associate column id with series id
		Map<String, String> columnIds2SeriesId = new Hashtable<String, String>();
		int i = 0;
		for (Entry<String,List<String>> entry: columnProperties2columnIds.entrySet()){
			String seriesId = "Series_" + (++i);
			for(String columnId: entry.getValue()){
				columnIds2SeriesId.put(columnId, seriesId);
			}
		}
		
		// Add series id property to each column
		for(Entry<String, List<PropertyValue>> entry: columnMetadata.entrySet()){
			String columnId = entry.getKey();
			String seriesId = columnIds2SeriesId.get(columnId);
			entry.getValue().add(
					new PropertyValue()
					.withCategory(MetadataProperties.DATAMATRIX_METADATA_COLUMN_DATASERIES)
					.withPropertyName(MetadataProperties.DATAMATRIX_METADATA_COLUMN_DATASERIES_SERIESID)
					.withPropertyUnit("")
					.withPropertyValue(seriesId)); 
		}
	}	

	
	

	private static void validateMetadata(Matrix2DMetadata metaData, List<String> sampleNames, List<String> rowNames) {
		
		//Check Description 
		int flag = 0;
		int errorCount = 0;
		
		for (PropertyValue p: metaData.getMatrixMetadata()) {
			if (p.getCategory().equals(MetadataProperties.DATAMATRIX_METADATA_TABLE_DESCRIPTION)) flag++;			
		}
		if (flag == 0) {
			if (errorCount == 0) printErrorStatus("Metadata validation");
			if (errorCount < 50) System.err.println ("Metadata must have a " + MetadataProperties.DATAMATRIX_METADATA_TABLE_DESCRIPTION + " entry");
			errorCount ++;
		} else if (flag > 1){
			if (errorCount == 0) printErrorStatus("Metadata validation");
			if (errorCount < 50) System.err.println ("Metadata must have only one " + MetadataProperties.DATAMATRIX_METADATA_TABLE_DESCRIPTION + " entry, but " + flag + " entries found");
			errorCount ++;
		}
		
		//Check Measurement for the entire table
		boolean statValues = false;
		flag = 0;
		for (PropertyValue p: metaData.getMatrixMetadata()) {
			if (p.getCategory().equals(MetadataProperties.DATAMATRIX_METADATA_TABLE_MEASUREMENT)&&p.getPropertyName().equals(MetadataProperties.DATAMATRIX_METADATA_TABLE_MEASUREMENT_VALUES)) {
				if (!MetadataProperties.DATAMATRIX_METADATA_TABLE_MEASUREMENT_VALUES_VALUE.contains(p.getPropertyValue())){
					if (errorCount == 0) printErrorStatus("Metadata validation");
					if (errorCount < 50) System.err.println (MetadataProperties.DATAMATRIX_METADATA_TABLE_MEASUREMENT + "_" + MetadataProperties.DATAMATRIX_METADATA_TABLE_MEASUREMENT_VALUES + " metadata entry contains illegal value " + p.getPropertyValue());
					errorCount ++;
				} else if (p.getPropertyValue().equals(MetadataProperties.DATAMATRIX_METADATA_TABLE_MEASUREMENT_VALUES_VALUE_STATVALUES)) {
					statValues = true;
				}
				flag++;
			}
		}
		if (flag == 0) {
			if (errorCount == 0) printErrorStatus("Metadata validation");
			if (errorCount < 50) System.err.println ("Metadata must have " + MetadataProperties.DATAMATRIX_METADATA_TABLE_MEASUREMENT + "_" + MetadataProperties.DATAMATRIX_METADATA_TABLE_MEASUREMENT_VALUES + " entry");
			errorCount ++;
		} else if (flag > 1){
			if (errorCount == 0) printErrorStatus("Metadata validation");
			if (errorCount < 50) System.err.println ("Metadata must have only one " + MetadataProperties.DATAMATRIX_METADATA_TABLE_MEASUREMENT + "_" + MetadataProperties.DATAMATRIX_METADATA_TABLE_MEASUREMENT_VALUES + " entry, , but it contains " + flag);
			errorCount ++;
		}

		if (statValues){
			for (String sampleName : sampleNames){
				flag = 0;
				try {
					for (PropertyValue p: metaData.getColumnMetadata().get(sampleName)){
						if (p.getCategory().equals(MetadataProperties.DATAMATRIX_METADATA_COLUMN_MEASUREMENT)&&p.getPropertyName().equals(MetadataProperties.DATAMATRIX_METADATA_COLUMN_MEASUREMENT_VALUETYPE)){
							if (!MetadataProperties.DATAMATRIX_METADATA_COLUMN_MEASUREMENT_VALUETYPE_VALUE.contains(p.getPropertyValue())){
								if (errorCount == 0) printErrorStatus("Metadata validation");
								if (errorCount < 50) System.err.println (MetadataProperties.DATAMATRIX_METADATA_COLUMN_MEASUREMENT + "_" + MetadataProperties.DATAMATRIX_METADATA_COLUMN_MEASUREMENT_VALUETYPE + " entry for column " + sampleName + " contains illegal value " + p.getPropertyValue());
								errorCount ++;
							}
							flag++;
						}
					}
				} catch (NullPointerException e) {
					if (errorCount == 0) printErrorStatus("Metadata validation");
					if (errorCount < 50) System.err.println ("Metadata entries for column " + sampleName + " are missing");
					errorCount ++;
				}
				if (flag == 0) {
					if (errorCount == 0) printErrorStatus("Metadata validation");
					if (errorCount < 50) System.err.println ("Metadata for column " + sampleName + " must have a " + MetadataProperties.DATAMATRIX_METADATA_COLUMN_MEASUREMENT + "_" + MetadataProperties.DATAMATRIX_METADATA_COLUMN_MEASUREMENT_VALUETYPE + " entry");
					errorCount ++;
				} else if (flag > 1) {
					if (errorCount == 0) printErrorStatus("Metadata validation");
					if (errorCount < 50) System.err.println ("Metadata for column " + sampleName + " must have only one " + MetadataProperties.DATAMATRIX_METADATA_COLUMN_MEASUREMENT + "_" + MetadataProperties.DATAMATRIX_METADATA_COLUMN_MEASUREMENT_VALUETYPE + " entry, but it contains " + flag);
					errorCount ++;
				}
			}
		}
		if (errorCount > 50) {
			throw new IllegalStateException("Cannot proceed with upload: metadata validation failed. " + errorCount + " errors were found, but only first 50 were displayed");
		} else if (errorCount > 0) {
			throw new IllegalStateException("Cannot proceed with upload: metadata validation failed");
		}
	 
	}

	private static void printErrorStatus(String message) {
		System.err.println("\n" + message + " failed. See detailed report for a list of errors.\n                                                                                                                                \n");
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
		if (inputFile == null){
			throw new IllegalStateException("Input file with extention .txt or .tsv was not "
					+ "found among: " + fileList);
		}
		return inputFile;
	}

}

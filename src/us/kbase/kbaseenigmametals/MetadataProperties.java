package us.kbase.kbaseenigmametals;

//import java.io.File;
//import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.Arrays;
import java.util.List;
import java.util.Properties;


public class MetadataProperties {

	public static String DATAMATRIX_METADATA_TABLE_DESCRIPTION;
	public static String DATAMATRIX_METADATA_TABLE_MEASUREMENT;
	public static String DATAMATRIX_METADATA_TABLE_MEASUREMENT_VALUES;
	public static List<String> DATAMATRIX_METADATA_TABLE_MEASUREMENT_VALUES_VALUE;
	public static String DATAMATRIX_METADATA_TABLE_MEASUREMENT_VALUES_VALUE_STATVALUES;
	public static String DATAMATRIX_METADATA_COLUMN_MEASUREMENT;
	public static String DATAMATRIX_METADATA_COLUMN_MEASUREMENT_VALUETYPE;
	public static List<String> DATAMATRIX_METADATA_COLUMN_MEASUREMENT_VALUETYPE_VALUE;
	public static String GROWTHMATRIX_METADATA_ROW_TIMESERIES;
	public static String GROWTHMATRIX_METADATA_ROW_TIMESERIES_TIME;
	public static List<String> GROWTHMATRIX_METADATA_ROW_TIMESERIES_TIME_UNIT;
	public static String GROWTHMATRIX_METADATA_COLUMN_CONDITION;
	public static List<String> GROWTHMATRIX_METADATA_COLUMN_CONDITION_UNIT;
	public static String DATAMATRIX_METADATA_COLUMN_DATASERIES;
	public static String DATAMATRIX_METADATA_COLUMN_DATASERIES_SERIESID;
	public static String CHROMATOGRAPHYMATRIX_METADATA_ROW_TIMESERIES;
	public static List<String> CHROMATOGRAPHYMATRIX_METADATA_ROW_TIMESERIES_TIME;
	public static List<String> CHROMATOGRAPHYMATRIX_METADATA_ROW_TIMESERIES_TIME_UNIT;
	public static String CHROMATOGRAPHYMATRIX_METADATA_COLUMN_MEASUREMENT;
	public static String CHROMATOGRAPHYMATRIX_METADATA_COLUMN_MEASUREMENT_INTENSITY;
	public static List<String> CHROMATOGRAPHYMATRIX_METADATA_COLUMN_MEASUREMENT_INTENSITY_UNIT;
	public static String SAMPLEPROPERTYMATRIX_METADATA_COLUMN_MEASUREMENT;
	public static String SAMPLEPROPERTYMATRIX_METADATA_COLUMN_MEASUREMENT_SUBSTANCE;
	public static List<String> SAMPLEPROPERTYMATRIX_METADATA_COLUMN_MEASUREMENT_SUBSTANCE_UNIT;
	public static String SAMPLEPROPERTYMATRIX_METADATA_ROW_SAMPLE;
	public static String SAMPLEPROPERTYMATRIX_METADATA_ROW_SAMPLE_ID;
	public static String SAMPLEPROPERTYMATRIX_METADATA_ROW_SAMPLE_WELLID;
	
	
	public static void startup() {
		
		//System.out.println(MetadataProperties.class.getClass().getResourceAsStream("/us/kbase/kbaseenigmametals/uploader.properties"));
		/*File propertiesFile;
		String kbTop = System.getenv("KB_TOP");
		if (!kbTop.substring(kbTop.length() - 1).equals("/")) {
			kbTop = kbTop + "/";
		}
		propertiesFile = new File (kbTop + "lib/jars/kbase/transform/uploader.properties");
		*/
		Properties prop = new Properties();
		InputStream input = null;
		 
		try {
	 
			//input = new FileInputStream(propertiesFile);
			input = MetadataProperties.class.getClass().getResourceAsStream("/us/kbase/kbaseenigmametals/uploader.properties");
			// load a properties file
			prop.load(input);
			// set metadata properties
			DATAMATRIX_METADATA_TABLE_DESCRIPTION = prop.getProperty("datamatrix.metadata.description");
			DATAMATRIX_METADATA_TABLE_MEASUREMENT = prop.getProperty("datamatrix.metadata.table.measurement");
			DATAMATRIX_METADATA_TABLE_MEASUREMENT_VALUES = prop.getProperty("datamatrix.metadata.table.measurement.values");
			DATAMATRIX_METADATA_TABLE_MEASUREMENT_VALUES_VALUE = Arrays.asList(prop.getProperty("datamatrix.metadata.table.measurement.values.value").split(",", 0));
			DATAMATRIX_METADATA_TABLE_MEASUREMENT_VALUES_VALUE_STATVALUES = prop.getProperty("datamatrix.metadata.table.measurement.values.value.statvalues");
			DATAMATRIX_METADATA_COLUMN_MEASUREMENT = prop.getProperty("datamatrix.metadata.column.measurement");
			DATAMATRIX_METADATA_COLUMN_MEASUREMENT_VALUETYPE = prop.getProperty("datamatrix.metadata.column.measurement.valuetype");
			DATAMATRIX_METADATA_COLUMN_MEASUREMENT_VALUETYPE_VALUE = Arrays.asList(prop.getProperty("datamatrix.metadata.column.measurement.valuetype.value").split(",", 0));
			DATAMATRIX_METADATA_COLUMN_DATASERIES = prop.getProperty("datamatrix.metadata.column.dataseries");
			DATAMATRIX_METADATA_COLUMN_DATASERIES_SERIESID = prop.getProperty("datamatrix.metadata.column.dataseries.seriesid");
			GROWTHMATRIX_METADATA_ROW_TIMESERIES = prop.getProperty("growthmatrix.metadata.row.timeseries");
			GROWTHMATRIX_METADATA_ROW_TIMESERIES_TIME = prop.getProperty("growthmatrix.metadata.row.timeseries.time");
			GROWTHMATRIX_METADATA_ROW_TIMESERIES_TIME_UNIT = Arrays.asList(prop.getProperty("growthmatrix.metadata.row.timeseries.time.unit").split(",", 0));
			GROWTHMATRIX_METADATA_COLUMN_CONDITION = prop.getProperty("growthmatrix.metadata.column.condition");
			GROWTHMATRIX_METADATA_COLUMN_CONDITION_UNIT = Arrays.asList(prop.getProperty("growthmatrix.metadata.column.condition.unit").split(",", 0));
			CHROMATOGRAPHYMATRIX_METADATA_ROW_TIMESERIES = prop.getProperty("chromatographymatrix.metadata.row.timeseries");
			CHROMATOGRAPHYMATRIX_METADATA_ROW_TIMESERIES_TIME = Arrays.asList(prop.getProperty("chromatographymatrix.metadata.row.timeseries.time"));
			CHROMATOGRAPHYMATRIX_METADATA_ROW_TIMESERIES_TIME_UNIT = Arrays.asList(prop.getProperty("chromatographymatrix.metadata.row.timeseries.time.unit").split(",", 0));
			CHROMATOGRAPHYMATRIX_METADATA_COLUMN_MEASUREMENT = prop.getProperty("chromatographymatrix.metadata.column.measurement");
			CHROMATOGRAPHYMATRIX_METADATA_COLUMN_MEASUREMENT_INTENSITY = prop.getProperty("chromatographymatrix.metadata.column.measurement.intensity");
			CHROMATOGRAPHYMATRIX_METADATA_COLUMN_MEASUREMENT_INTENSITY_UNIT = Arrays.asList(prop.getProperty("chromatographymatrix.metadata.column.measurement.intensity.unit").split(",", 0));
			SAMPLEPROPERTYMATRIX_METADATA_COLUMN_MEASUREMENT = prop.getProperty("samplepropertymatrix.metadata.column.measurement");
			SAMPLEPROPERTYMATRIX_METADATA_COLUMN_MEASUREMENT_SUBSTANCE = prop.getProperty("samplepropertymatrix.metadata.column.measurement.substance");
			SAMPLEPROPERTYMATRIX_METADATA_COLUMN_MEASUREMENT_SUBSTANCE_UNIT = Arrays.asList(prop.getProperty("samplepropertymatrix.metadata.column.measurement.substance.unit").split(",", 0));
			SAMPLEPROPERTYMATRIX_METADATA_ROW_SAMPLE = prop.getProperty("samplepropertymatrix.metadata.row.sample");
			SAMPLEPROPERTYMATRIX_METADATA_ROW_SAMPLE_ID = prop.getProperty("samplepropertymatrix.metadata.row.sample.id");
			SAMPLEPROPERTYMATRIX_METADATA_ROW_SAMPLE_WELLID = prop.getProperty("samplepropertymatrix.metadata.row.sample.wellid");
			
			//System.out.println(WELLSAMPLEMATRIX_METADATA_ROW_SAMPLE_WELLID);
	 
		} catch (IOException ex) {
			ex.printStackTrace();
		} finally {
			if (input != null) {
				try {
					input.close();
				} catch (IOException e) {
					e.printStackTrace();
				}
			}
		}
	}

}

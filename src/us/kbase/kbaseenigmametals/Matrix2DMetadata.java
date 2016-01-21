
package us.kbase.kbaseenigmametals;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import javax.annotation.Generated;
import com.fasterxml.jackson.annotation.JsonAnyGetter;
import com.fasterxml.jackson.annotation.JsonAnySetter;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonPropertyOrder;


/**
 * <p>Original spec-file type: Matrix2DMetadata</p>
 * <pre>
 * Metadata for data matrix
 * </pre>
 * 
 */
@JsonInclude(JsonInclude.Include.NON_NULL)
@Generated("com.googlecode.jsonschema2pojo")
@JsonPropertyOrder({
    "row_metadata",
    "column_metadata",
    "matrix_metadata"
})
public class Matrix2DMetadata {

    @JsonProperty("row_metadata")
    private Map<String, List<us.kbase.kbaseenigmametals.PropertyValue>> rowMetadata;
    @JsonProperty("column_metadata")
    private Map<String, List<us.kbase.kbaseenigmametals.PropertyValue>> columnMetadata;
    @JsonProperty("matrix_metadata")
    private List<us.kbase.kbaseenigmametals.PropertyValue> matrixMetadata;
    private Map<java.lang.String, Object> additionalProperties = new HashMap<java.lang.String, Object>();

    @JsonProperty("row_metadata")
    public Map<String, List<us.kbase.kbaseenigmametals.PropertyValue>> getRowMetadata() {
        return rowMetadata;
    }

    @JsonProperty("row_metadata")
    public void setRowMetadata(Map<String, List<us.kbase.kbaseenigmametals.PropertyValue>> rowMetadata) {
        this.rowMetadata = rowMetadata;
    }

    public Matrix2DMetadata withRowMetadata(Map<String, List<us.kbase.kbaseenigmametals.PropertyValue>> rowMetadata) {
        this.rowMetadata = rowMetadata;
        return this;
    }

    @JsonProperty("column_metadata")
    public Map<String, List<us.kbase.kbaseenigmametals.PropertyValue>> getColumnMetadata() {
        return columnMetadata;
    }

    @JsonProperty("column_metadata")
    public void setColumnMetadata(Map<String, List<us.kbase.kbaseenigmametals.PropertyValue>> columnMetadata) {
        this.columnMetadata = columnMetadata;
    }

    public Matrix2DMetadata withColumnMetadata(Map<String, List<us.kbase.kbaseenigmametals.PropertyValue>> columnMetadata) {
        this.columnMetadata = columnMetadata;
        return this;
    }

    @JsonProperty("matrix_metadata")
    public List<us.kbase.kbaseenigmametals.PropertyValue> getMatrixMetadata() {
        return matrixMetadata;
    }

    @JsonProperty("matrix_metadata")
    public void setMatrixMetadata(List<us.kbase.kbaseenigmametals.PropertyValue> matrixMetadata) {
        this.matrixMetadata = matrixMetadata;
    }

    public Matrix2DMetadata withMatrixMetadata(List<us.kbase.kbaseenigmametals.PropertyValue> matrixMetadata) {
        this.matrixMetadata = matrixMetadata;
        return this;
    }

    @JsonAnyGetter
    public Map<java.lang.String, Object> getAdditionalProperties() {
        return this.additionalProperties;
    }

    @JsonAnySetter
    public void setAdditionalProperties(java.lang.String name, Object value) {
        this.additionalProperties.put(name, value);
    }

    @Override
    public java.lang.String toString() {
        return ((((((((("Matrix2DMetadata"+" [rowMetadata=")+ rowMetadata)+", columnMetadata=")+ columnMetadata)+", matrixMetadata=")+ matrixMetadata)+", additionalProperties=")+ additionalProperties)+"]");
    }

}

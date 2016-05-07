
package us.kbase.kbaseenigmametals;

import java.util.HashMap;
import java.util.Map;
import javax.annotation.Generated;
import com.fasterxml.jackson.annotation.JsonAnyGetter;
import com.fasterxml.jackson.annotation.JsonAnySetter;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonPropertyOrder;


/**
 * <p>Original spec-file type: PropertyValue</p>
 * <pre>
 * Single piece of metadata
 *       @optional property_unit
 * </pre>
 * 
 */
@JsonInclude(JsonInclude.Include.NON_NULL)
@Generated("com.googlecode.jsonschema2pojo")
@JsonPropertyOrder({
    "category",
    "property_name",
    "property_unit",
    "property_value"
})
public class PropertyValue {

    @JsonProperty("category")
    private String category;
    @JsonProperty("property_name")
    private String propertyName;
    @JsonProperty("property_unit")
    private String propertyUnit;
    @JsonProperty("property_value")
    private String propertyValue;
    private Map<String, Object> additionalProperties = new HashMap<String, Object>();

    @JsonProperty("category")
    public String getCategory() {
        return category;
    }

    @JsonProperty("category")
    public void setCategory(String category) {
        this.category = category;
    }

    public PropertyValue withCategory(String category) {
        this.category = category;
        return this;
    }

    @JsonProperty("property_name")
    public String getPropertyName() {
        return propertyName;
    }

    @JsonProperty("property_name")
    public void setPropertyName(String propertyName) {
        this.propertyName = propertyName;
    }

    public PropertyValue withPropertyName(String propertyName) {
        this.propertyName = propertyName;
        return this;
    }

    @JsonProperty("property_unit")
    public String getPropertyUnit() {
        return propertyUnit;
    }

    @JsonProperty("property_unit")
    public void setPropertyUnit(String propertyUnit) {
        this.propertyUnit = propertyUnit;
    }

    public PropertyValue withPropertyUnit(String propertyUnit) {
        this.propertyUnit = propertyUnit;
        return this;
    }

    @JsonProperty("property_value")
    public String getPropertyValue() {
        return propertyValue;
    }

    @JsonProperty("property_value")
    public void setPropertyValue(String propertyValue) {
        this.propertyValue = propertyValue;
    }

    public PropertyValue withPropertyValue(String propertyValue) {
        this.propertyValue = propertyValue;
        return this;
    }

    @JsonAnyGetter
    public Map<String, Object> getAdditionalProperties() {
        return this.additionalProperties;
    }

    @JsonAnySetter
    public void setAdditionalProperties(String name, Object value) {
        this.additionalProperties.put(name, value);
    }

    @Override
    public String toString() {
        return ((((((((((("PropertyValue"+" [category=")+ category)+", propertyName=")+ propertyName)+", propertyUnit=")+ propertyUnit)+", propertyValue=")+ propertyValue)+", additionalProperties=")+ additionalProperties)+"]");
    }

}

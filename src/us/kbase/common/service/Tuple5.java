package us.kbase.common.service;

import java.util.HashMap;
import java.util.Map;
import com.fasterxml.jackson.annotation.JsonAnyGetter;
import com.fasterxml.jackson.annotation.JsonAnySetter;

public class Tuple5 <T1, T2, T3, T4, T5> {
    private T1 e1;
    private T2 e2;
    private T3 e3;
    private T4 e4;
    private T5 e5;
    private Map<String, Object> additionalProperties = new HashMap<String, Object>();

    public T1 getE1() {
        return e1;
    }

    public void setE1(T1 e1) {
        this.e1 = e1;
    }

    public Tuple5<T1, T2, T3, T4, T5> withE1(T1 e1) {
        this.e1 = e1;
        return this;
    }

    public T2 getE2() {
        return e2;
    }

    public void setE2(T2 e2) {
        this.e2 = e2;
    }

    public Tuple5<T1, T2, T3, T4, T5> withE2(T2 e2) {
        this.e2 = e2;
        return this;
    }

    public T3 getE3() {
        return e3;
    }

    public void setE3(T3 e3) {
        this.e3 = e3;
    }

    public Tuple5<T1, T2, T3, T4, T5> withE3(T3 e3) {
        this.e3 = e3;
        return this;
    }

    public T4 getE4() {
        return e4;
    }

    public void setE4(T4 e4) {
        this.e4 = e4;
    }

    public Tuple5<T1, T2, T3, T4, T5> withE4(T4 e4) {
        this.e4 = e4;
        return this;
    }

    public T5 getE5() {
        return e5;
    }

    public void setE5(T5 e5) {
        this.e5 = e5;
    }

    public Tuple5<T1, T2, T3, T4, T5> withE5(T5 e5) {
        this.e5 = e5;
        return this;
    }

    @Override
    public String toString() {
        return "Tuple5 [e1=" + e1 + ", e2=" + e2 + ", e3=" + e3 + ", e4=" + e4 + ", e5=" + e5 + "]";
    }

    @JsonAnyGetter
    public Map<String, Object> getAdditionalProperties() {
        return this.additionalProperties;
    }

    @JsonAnySetter
    public void setAdditionalProperties(String name, Object value) {
        this.additionalProperties.put(name, value);
    }
}

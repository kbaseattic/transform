package us.kbase.common.service;

import java.util.HashMap;
import java.util.Map;
import com.fasterxml.jackson.annotation.JsonAnyGetter;
import com.fasterxml.jackson.annotation.JsonAnySetter;

public class Tuple11 <T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11> {
    private T1 e1;
    private T2 e2;
    private T3 e3;
    private T4 e4;
    private T5 e5;
    private T6 e6;
    private T7 e7;
    private T8 e8;
    private T9 e9;
    private T10 e10;
    private T11 e11;
    private Map<String, Object> additionalProperties = new HashMap<String, Object>();

    public T1 getE1() {
        return e1;
    }

    public void setE1(T1 e1) {
        this.e1 = e1;
    }

    public Tuple11<T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11> withE1(T1 e1) {
        this.e1 = e1;
        return this;
    }

    public T2 getE2() {
        return e2;
    }

    public void setE2(T2 e2) {
        this.e2 = e2;
    }

    public Tuple11<T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11> withE2(T2 e2) {
        this.e2 = e2;
        return this;
    }

    public T3 getE3() {
        return e3;
    }

    public void setE3(T3 e3) {
        this.e3 = e3;
    }

    public Tuple11<T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11> withE3(T3 e3) {
        this.e3 = e3;
        return this;
    }

    public T4 getE4() {
        return e4;
    }

    public void setE4(T4 e4) {
        this.e4 = e4;
    }

    public Tuple11<T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11> withE4(T4 e4) {
        this.e4 = e4;
        return this;
    }

    public T5 getE5() {
        return e5;
    }

    public void setE5(T5 e5) {
        this.e5 = e5;
    }

    public Tuple11<T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11> withE5(T5 e5) {
        this.e5 = e5;
        return this;
    }

    public T6 getE6() {
        return e6;
    }

    public void setE6(T6 e6) {
        this.e6 = e6;
    }

    public Tuple11<T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11> withE6(T6 e6) {
        this.e6 = e6;
        return this;
    }

    public T7 getE7() {
        return e7;
    }

    public void setE7(T7 e7) {
        this.e7 = e7;
    }

    public Tuple11<T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11> withE7(T7 e7) {
        this.e7 = e7;
        return this;
    }

    public T8 getE8() {
        return e8;
    }

    public void setE8(T8 e8) {
        this.e8 = e8;
    }

    public Tuple11<T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11> withE8(T8 e8) {
        this.e8 = e8;
        return this;
    }

    public T9 getE9() {
        return e9;
    }

    public void setE9(T9 e9) {
        this.e9 = e9;
    }

    public Tuple11<T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11> withE9(T9 e9) {
        this.e9 = e9;
        return this;
    }

    public T10 getE10() {
        return e10;
    }

    public void setE10(T10 e10) {
        this.e10 = e10;
    }

    public Tuple11<T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11> withE10(T10 e10) {
        this.e10 = e10;
        return this;
    }

    public T11 getE11() {
        return e11;
    }

    public void setE11(T11 e11) {
        this.e11 = e11;
    }

    public Tuple11<T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11> withE11(T11 e11) {
        this.e11 = e11;
        return this;
    }

    @Override
    public String toString() {
        return "Tuple11 [e1=" + e1 + ", e2=" + e2 + ", e3=" + e3 + ", e4=" + e4 + ", e5=" + e5 + ", e6=" + e6 + ", e7=" + e7 + ", e8=" + e8 + ", e9=" + e9 + ", e10=" + e10 + ", e11=" + e11 + "]";
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
